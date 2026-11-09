"""Road network for mesh generation: chains (maximal runs through degree-2 nodes) with per-station
cross-sections derived from graph tags (lanes, oneway, highway class, BDOT10k width), sidewalks from
parallel OSM footways, medians from opposite one-way carriageways, bridges from `bridge`/`layer`.

All coordinates are region-local metres: E = x - origin.x, N = y - origin.y (ADR 0003).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import shapely
from shapely.geometry import LineString, Point

from . import standards as S
from .geom import Polyline, cumlen, smooth_1d, smooth_open

DENSE = 0.5          # m, dense polyline spacing used for evaluation
SURFACE_MAT = {"asphalt": "road_asphalt", "paved": "road_asphalt", "concrete": "road_concrete",
               "concrete:plates": "road_concrete", "paving_stones": "road_paving", "sett": "road_sett",
               "cobblestone": "road_sett", "unhewn_cobblestone": "road_sett", "compacted": "road_gravel",
               "gravel": "road_gravel", "fine_gravel": "road_gravel", "unpaved": "road_gravel",
               "ground": "road_gravel", "dirt": "road_gravel"}

# side profile families
URBAN, ISLAND, RURAL, MEDIAN_RURAL = 0, 1, 2, 3
WALK_MATS = ["curb_concrete", "sidewalk_paving", "bridge_concrete", "verge_grass"]


@dataclass
class EdgeSection:
    edge_id: str
    highway: str
    cls: str
    oneway: bool
    lanes: int
    lanes_fwd: int
    lanes_bwd: int
    lane_w: float
    edge_strip: float
    width: float               # carriageway, gutter to gutter
    width_src: str
    surface_mat: str
    bridge: bool
    layer: int
    roundabout: bool
    maxspeed: float | None
    turn_fwd: list | None
    turn_bwd: list | None
    side_override: dict = field(default_factory=dict)     # {"left"/"right": kind} in OSM edge direction
    provenance: dict = field(default_factory=dict)


def _v(a, k, default=None):
    return a[k]["v"] if k in a and a[k]["v"] is not None else default


def edge_section(e: dict) -> EdgeSection:
    a = e["attrs"]
    hw = _v(a, "highway")
    cls = S.road_class(hw)
    oneway = _v(a, "oneway", "no") != "no"
    lanes = max(1, int(_v(a, "lanes", 1 if oneway else 2)))
    if oneway:
        fwd, bwd = lanes, 0
    else:
        fwd = int(_v(a, "lanes:forward", 0) or 0)
        bwd = int(_v(a, "lanes:backward", 0) or 0)
        if fwd + bwd != lanes:
            fwd = max(1, lanes // 2 + lanes % 2)
            bwd = max(1, lanes - fwd)
            lanes = fwd + bwd
    roundabout = _v(a, "junction") in ("roundabout", "circular")
    edge = 0.0 if roundabout else S.EDGE_STRIP[cls]
    std, diff = S.LANE_WIDTH[cls]
    bw = _v(a, "width")
    wsrc = "PTB2022 §17 ust.1 standard"
    prov = {}
    if lanes == 1:
        edge = 0.0
        lw = 4.5 if hw.endswith("_link") else S.SINGLE_LANE_DEFAULT
        wsrc = "PTB2022 §17 ust.3 (>=3.50) + WORKING_VALUE"
        if bw:
            lw = min(max(bw, S.SINGLE_LANE_MIN), 5.5)
            wsrc = "bdot10k (clamped 3.50-5.50)"
    else:
        lw = std
        if bw:
            per = (bw - 2 * edge) / lanes
            if 2.4 <= per <= 4.75:
                lw = min(max(per, diff), std + 0.25)
                wsrc = "bdot10k (clamped to PTB2022 §17 ust.1 range)"
            else:
                prov["width_rejected"] = {"bdot_width": bw, "per_lane": round(per, 2)}
    width = lanes * lw + 2 * edge
    surf = _v(a, "surface", "asphalt")
    tl = _v(a, "turn:lanes")
    tf = _v(a, "turn:lanes:forward")
    tb = _v(a, "turn:lanes:backward")
    split = (lambda t: t.split("|") if t else None)
    ms = _v(a, "maxspeed")
    return EdgeSection(
        edge_id=e["id"], highway=hw, cls=cls, oneway=oneway, lanes=lanes, lanes_fwd=fwd, lanes_bwd=bwd,
        lane_w=round(lw, 3), edge_strip=edge, width=round(width, 3), width_src=wsrc,
        surface_mat=SURFACE_MAT.get(surf, "road_asphalt"), bridge=bool(_v(a, "bridge")),
        layer=int(_v(a, "layer", 0) or 0), roundabout=roundabout, maxspeed=float(ms) if ms else None,
        turn_fwd=split(tl if oneway else tf), turn_bwd=split(None if oneway else tb), provenance=prov)


@dataclass
class Chain:
    id: str
    node_a: str
    node_b: str
    edges: list            # [(edge_id, reversed)]
    raw: np.ndarray        # raw polyline (local)
    raw_spans: list        # [(s0, s1, edge_id, reversed)] in raw arc length
    closed: bool = False
    line: Polyline | None = None
    # per dense sample arrays
    sec_idx: np.ndarray | None = None
    hw: np.ndarray | None = None
    dirn: np.ndarray | None = None        # +1 travel along chain, -1 against, 0 two-way
    bridge: np.ndarray | None = None
    roundabout: bool = False
    side: dict = field(default_factory=dict)  # "L"/"R" -> dict of arrays
    z: np.ndarray | None = None           # centre height per dense sample
    e: np.ndarray | None = None           # one-sided crossfall (z = zc + e*l); nan = roof profile
    t_a: float = 0.0                      # trims at ends (from junction patches)
    t_b: float = 0.0
    m_lat: int = 2                        # lateral subdivisions of the carriageway (even)
    meta: dict = field(default_factory=dict)

    @property
    def length(self):
        return self.line.length

    def idx(self, s):
        return np.clip(np.rint(np.asarray(s) / DENSE).astype(int), 0, len(self.line.s) - 1)

    def interp(self, arr, s):
        return np.interp(np.clip(s, 0, self.length), self.line.s, arr)

    def hw_at(self, s):
        return self.interp(self.hw, s)

    def zc(self, s):
        return self.interp(self.z, s)

    def crossfall_z(self, s, lat):
        """Surface height on the carriageway at station s, lateral lat (left +)."""
        s = np.asarray(s, float)
        lat = np.asarray(lat, float)
        e = self.interp(np.nan_to_num(self.e, nan=0.0), s)
        roof = self.interp(np.isnan(self.e).astype(float), s) > 0.5
        hw = self.hw_at(s)
        latc = np.clip(lat, -hw, hw)
        return self.zc(s) + np.where(roof, -S.CROSSFALL * np.abs(latc), e * latc)

    def grade(self, s):
        return np.interp(np.clip(s, 0, self.length), self.line.s, np.gradient(self.z, self.line.s))

    def section(self, s, sections):
        return sections[int(self.sec_idx[self.idx(s)])]


@dataclass
class Network:
    nodes: dict            # id -> {"xy": np.array, "deg": int, ...}
    sections: dict         # edge_id -> EdgeSection
    sec_list: list         # index -> EdgeSection
    chains: list           # [Chain]
    origin: tuple
    overrides_applied: list = field(default_factory=list)
    overrides_stale: list = field(default_factory=list)


def load(graph: dict, origin, overrides: list | None = None) -> Network:
    ox, oy = origin
    nodes = {}
    for n in graph["nodes"]:
        nodes[n["id"]] = {"id": n["id"], "xy": np.array([n["x"] - ox, n["y"] - oy]), "deg": 0,
                          "feature": n.get("feature"), "signals": bool(n.get("signals_nearby")),
                          "boundary": bool(n.get("boundary")), "z_terrain": n.get("z_terrain")}
    edges = {}
    for e in sorted(graph["edges"], key=lambda e: e["id"]):
        g = np.array(e["geometry"], float) - np.array([ox, oy])
        a, b = e["from"], e["to"]
        if e["attrs"]["oneway"]["v"] == "-1":      # normalise: geometry runs in travel direction
            g, a, b = g[::-1].copy(), b, a
            e = dict(e)
            e["attrs"] = dict(e["attrs"])
            e["attrs"]["oneway"] = {"v": "yes", "src": "derived", "conf": "high"}
        if len(g) < 2 or cumlen(g)[-1] < 0.05:
            continue
        edges[e["id"]] = (e, g, a, b)
        nodes[a]["deg"] += 1
        nodes[b]["deg"] += 1
    sections = {eid: edge_section(e) for eid, (e, _, _, _) in edges.items()}
    net = Network(nodes=nodes, sections=sections, sec_list=[], chains=[], origin=(ox, oy))
    apply_edge_overrides(net, edges, overrides or [])
    net.sec_list = [sections[k] for k in sorted(sections)]
    sec_index = {s.edge_id: i for i, s in enumerate(net.sec_list)}
    net.chains = build_chains(nodes, edges)
    for c in net.chains:
        prepare_chain(c, net, sec_index)
    return net


def apply_edge_overrides(net: Network, edges, overrides):
    for ov in overrides:
        tgt = ov.get("target", {})
        ids = []
        if "building" in tgt or ov.get("kind"):
            continue                       # streetscape overrides (buildings, paved areas): streetscape.stage
        if "edge" in tgt:
            ids = [tgt["edge"]] if tgt["edge"] in net.sections else []
        elif "osm_way" in tgt:
            ways = tgt["osm_way"] if isinstance(tgt["osm_way"], list) else [tgt["osm_way"]]
            ways = {int(w) for w in ways}
            ids = sorted(k for k, (e, *_r) in edges.items() if e["osm_way"] in ways)
        elif "node" in tgt:
            if tgt["node"] in net.nodes:
                net.nodes[tgt["node"]].setdefault("override", {}).update(ov.get("set", {}))
                net.overrides_applied.append({"id": ov["id"], "targets": [tgt["node"]]})
            else:
                net.overrides_stale.append(ov["id"])
            continue
        if not ids:
            net.overrides_stale.append(ov["id"])
            continue
        for eid in ids:
            sec = net.sections[eid]
            st = ov.get("set", {})
            if "lanes" in st:
                sec.lanes = int(st["lanes"])
                if not sec.oneway:
                    sec.lanes_fwd = sec.lanes - sec.lanes // 2
                    sec.lanes_bwd = sec.lanes // 2
                else:
                    sec.lanes_fwd = sec.lanes
            if "lane_width" in st:
                sec.lane_w = float(st["lane_width"])
            if "edge_strip" in st:
                sec.edge_strip = float(st["edge_strip"])
            if any(k in st for k in ("lanes", "lane_width", "edge_strip")):
                sec.width = round(sec.lanes * sec.lane_w + 2 * sec.edge_strip, 3)
                sec.width_src = f"authored_override:{ov['id']}"
            for side in ("left", "right"):
                if f"side_{side}" in st:
                    sec.side_override[side] = st[f"side_{side}"]
            if "surface" in st:
                sec.surface_mat = SURFACE_MAT.get(st["surface"], "road_asphalt")
            sec.provenance["authored_override"] = ov["id"]
        net.overrides_applied.append({"id": ov["id"], "targets": ids})


def build_chains(nodes, edges) -> list[Chain]:
    inc = {}
    for eid in sorted(edges):
        _, _, a, b = edges[eid]
        inc.setdefault(a, []).append(eid)
        inc.setdefault(b, []).append(eid)

    def through(n):
        return nodes[n]["deg"] == 2 and len(inc.get(n, [])) == 2

    used = set()
    chains = []
    for eid in sorted(edges):
        if eid in used:
            continue
        used.add(eid)
        _, g, a, b = edges[eid]
        seq = [(eid, False)]
        # extend forward from b
        cur = b
        closed = False
        while through(cur):
            nxt = [x for x in inc[cur] if x not in used]
            if not nxt:
                closed = cur == a
                break
            x = nxt[0]
            used.add(x)
            _, _, xa, xb = edges[x]
            rev = xb == cur
            seq.append((x, rev))
            cur = xa if rev else xb
        end_b = cur
        cur = a
        while not closed and through(cur):
            nxt = [x for x in inc[cur] if x not in used]
            if not nxt:
                break
            x = nxt[0]
            used.add(x)
            _, _, xa, xb = edges[x]
            rev = xa == cur          # we prepend, so the edge must end at cur
            seq.insert(0, (x, rev))
            cur = xb if rev else xa
        end_a = cur
        if end_a == end_b and len(seq) > 1:
            closed = True
        # orient deterministically: start at the smaller node id
        if not closed and end_b < end_a:
            seq = [(x, not r) for x, r in reversed(seq)]
            end_a, end_b = end_b, end_a
        pts, spans, s0 = [], [], 0.0
        for x, r in seq:
            g = edges[x][1][::-1] if r else edges[x][1]
            L = float(cumlen(g)[-1])
            spans.append((s0, s0 + L, x, r))
            s0 += L
            pts.extend(g.tolist() if not pts else g[1:].tolist())
        cid = "c:" + min(x for x, _ in seq)
        chains.append(Chain(id=cid, node_a=end_a, node_b=end_b, edges=seq, raw=np.array(pts),
                            raw_spans=spans, closed=closed))
    chains.sort(key=lambda c: c.id)
    return chains


def prepare_chain(c: Chain, net: Network, sec_index: dict):
    secs = [net.sections[x] for x, _ in c.edges]
    wmax = max(s.width for s in secs)
    sigma = 2.0 + 0.2 * wmax
    if any(s.roundabout for s in secs):
        sigma = 1.5
    dense = smooth_open(c.raw, sigma, DENSE) if len(c.raw) > 2 else smooth_open(c.raw, 0, DENSE)
    c.line = Polyline(dense)
    L_raw = c.raw_spans[-1][1]
    s_raw = c.line.s * (L_raw / max(c.line.length, 1e-9))
    k = np.searchsorted([sp[1] for sp in c.raw_spans], s_raw, side="left")
    k = np.clip(k, 0, len(c.raw_spans) - 1)
    c.sec_idx = np.array([sec_index[c.raw_spans[i][2]] for i in k])
    rev = np.array([c.raw_spans[i][3] for i in k])
    sl = net.sec_list
    hw = np.array([sl[i].width / 2 for i in c.sec_idx])
    one = np.array([sl[i].oneway for i in c.sec_idx])
    c.dirn = np.where(one, np.where(rev, -1, 1), 0)
    c.bridge = np.array([sl[i].bridge for i in c.sec_idx])
    c.roundabout = bool(any(s.roundabout for s in secs))
    # width transitions: PTB2022 §17 ust.6 asks for smooth changes -> 15 m smoothing (WORKING_VALUE)
    c.hw = smooth_1d(hw, 7.5 / DENSE) if len(hw) > 3 else hw
    c.meta["rev"] = rev
    m = max(2, int(math.ceil(2 * float(c.hw.max()) / 1.75)))
    c.m_lat = m + (m % 2)          # even -> the crown (lat 0) is always a vertex


# --------------------------------------------------------------------------------------------
def assign_sides(net: Network, footways: list, built_up: bool = True, walkways: list | None = None,
                 yards=None):
    """Per-station side profile parameters for every chain (left 'L' and right 'R' of chain direction)."""
    # one-way carriageways (for median detection)
    ow_lines, ow_meta = [], []
    for c in net.chains:
        if (c.dirn != 0).all():
            ow_lines.append(LineString(c.line.p))
            ow_meta.append(c)
    ow_tree = shapely.STRtree(ow_lines) if ow_lines else None
    ft_tree = shapely.STRtree(footways) if footways else None
    wk_tree = shapely.STRtree(walkways) if walkways else ft_tree

    for c in net.chains:
        n = len(c.line.s)
        step = max(1, int(4.0 / DENSE))
        idx = np.arange(0, n, step)
        if idx[-1] != n - 1:
            idx = np.append(idx, n - 1)
        # rural cross-section (no kerbs: paved shoulder + verge/ditch, PTB2022 § 23 ust. 10) on fast GP/G roads
        # with no footway within RURAL_FOOT_M on either side (urban kerbed streets keep URBAN). WORKING_VALUE rule.
        sec_mid = net.sec_list[int(c.sec_idx[len(c.sec_idx) // 2])]
        fast = (built_up and sec_mid.cls in ("GP", "G", "S", "A") and (sec_mid.maxspeed or 50) >= S.RURAL_MIN_SPEED
                and not c.roundabout and not c.bridge.all() and wk_tree is not None)
        rural_d = {"L": np.zeros(n, bool), "R": np.zeros(n, bool)}
        if fast:
            win = max(1, int(round(30.0 / 4.0)))
            for side_, sg in (("L", 1.0), ("R", -1.0)):
                hits = np.zeros(len(idx))
                for j, i in enumerate(idx):
                    q = Point(*(c.line.p[i] + c.line.n[i] * sg * (c.hw[i] + S.RURAL_FOOT_M / 2)))
                    hits[j] = 1.0 if len(wk_tree.query(q.buffer(S.RURAL_FOOT_M / 2 + 1.0))) else 0.0
                hs = np.array([hits[max(0, j - win):j + win + 1].mean() for j in range(len(idx))]) < 0.2
                rural_d[side_] = np.interp(np.arange(n), idx, hs.astype(float)) > 0.5
        c.meta["rural"] = {k: round(float(v.mean()), 2) for k, v in rural_d.items()}
        for side, sgn in (("L", 1.0), ("R", -1.0)):
            walk = np.zeros(len(idx))
            median = np.zeros(len(idx))
            for j, i in enumerate(idx):
                p = c.line.p[i]
                nrm = c.line.n[i] * sgn
                hw = c.hw[i]
                if ft_tree is not None:
                    q = Point(*(p + nrm * (hw + S.KERB_TOP_W + 1.1)))
                    near = ft_tree.query(q.buffer(1.4))
                    walk[j] = 1.0 if len(near) and min(footways[k].distance(q) for k in near) <= 1.4 else 0.0
                if c.dirn[i] != 0 and ow_tree is not None:
                    tdir = c.line.t[i] * c.dirn[i]
                    for dist in (3.0, 6.0, 10.0, 15.0, 22.0):
                        q = Point(*(p + nrm * (hw + dist)))
                        hit = False
                        for k in ow_tree.query(q.buffer(3.0)):
                            oc = ow_meta[int(k)]
                            if oc is c:
                                continue
                            s_o, lat_o = oc.line.project(np.array([q.x, q.y]))
                            if abs(lat_o) > oc.hw_at(s_o) + 1.5:
                                continue
                            io = oc.idx(s_o)
                            to = oc.line.t[io] * oc.dirn[io]
                            if float(np.dot(to, tdir)) < -0.8:
                                hit = True
                                break
                        if hit:
                            median[j] = 1.0
                            break
            # majority filter over ~40 m
            win = max(1, int(round(20.0 / 4.0)))
            walk_s = np.array([walk[max(0, j - win):j + win + 1].mean() for j in range(len(idx))]) > 0.45
            med_s = np.array([median[max(0, j - win):j + win + 1].mean() for j in range(len(idx))]) > 0.45
            walk_d = np.interp(np.arange(n), idx, walk_s.astype(float)) > 0.5
            med_d = np.interp(np.arange(n), idx, med_s.astype(float)) > 0.5
            kind = np.where(rural_d[side] | (not built_up), RURAL, URBAN)
            h = np.full(n, S.KERB_HEIGHT)
            w = np.where(walk_d & ~med_d, S.SIDEWALK_W, 0.0)
            mat = np.where(walk_d & ~med_d, 1, 0)
            depth = np.full(n, S.FLANGE_DEPTH)
            # service roads running through a paved yard (BDOT10k plac / parking): no kerb, flush with the yard
            if yards is not None and sec_mid.cls == "D":
                inyard = np.zeros(len(idx))
                for jj, i in enumerate(idx):
                    q = c.line.p[i] + c.line.n[i] * sgn * (c.hw[i] + 2.0)
                    inyard[jj] = 1.0 if yards.contains(Point(*q)) else 0.0
                win = max(1, int(round(12.0 / 4.0)))
                ys = np.array([inyard[max(0, jj - win):jj + win + 1].mean() for jj in range(len(idx))]) > 0.5
                yd = np.interp(np.arange(n), idx, ys.astype(float)) > 0.5
                h[yd], w[yd] = 0.0, 0.0
                walk_d = walk_d & ~yd
            # explicit overrides (in OSM edge direction -> convert to chain side)
            for i_sec in np.unique(c.sec_idx):
                sec = net.sec_list[int(i_sec)]
                if not sec.side_override:
                    continue
                m = c.sec_idx == i_sec
                rev = bool(c.meta["rev"][m][0])
                osm_side = {"L": "left", "R": "right"}[side]
                if rev:
                    osm_side = {"left": "right", "right": "left"}[osm_side]
                kd = sec.side_override.get(osm_side)
                if kd == "sidewalk":
                    w[m], mat[m] = S.SIDEWALK_W, 1
                elif kd in ("verge", "median"):
                    w[m], mat[m] = 0.0, 0
                elif kd == "flush":           # paved yard / no kerb: flat edge strip at road level
                    h[m], w[m], mat[m] = 0.0, 0.0, 0
            other = rural_d["L" if side == "R" else "R"]
            fast_med = fast and (sec_mid.maxspeed or 50) >= 90
            kind[med_d] = np.where(other[med_d] | fast_med, MEDIAN_RURAL, URBAN)
            if c.roundabout and side == ("L" if (c.dirn > 0).mean() >= 0.5 else "R"):
                kind[:] = ISLAND
                w[:] = S.ROUNDABOUT_APRON_W
                mat[:] = 0
            # bridges: kerb 0.20 + cap 1.50 + fascia = deck thickness
            br = c.bridge
            kind[br] = URBAN
            h[br] = S.BRIDGE_KERB_H
            w[br] = S.BRIDGE_CAP_W
            mat[br] = 2
            depth[br] = S.BRIDGE_DECK_THICKNESS + S.BRIDGE_KERB_H
            sig = 2.0 / DENSE
            c.side[side] = {"kind": kind, "h": smooth_1d(h, sig), "w": smooth_1d(w, sig), "mat": mat,
                            "depth": smooth_1d(depth, sig), "walk": walk_d, "median": med_d}


def side_profile(kind: int, h: float, w: float, depth: float, mat: int):
    """Profile as list of (u0, dz0, u1, dz1, material) from the gutter outward (u >= 0).

    The topology (number of segments) depends only on `kind`, so stations of one family can be
    connected into strips and interpolated.
    """
    m = WALK_MATS[mat]
    if kind == ISLAND:
        ha = S.KERB_HEIGHT_APRON
        ap = w
        top = ha + 0.02 * ap
        return [(0.0, 0.0, 0.0, ha, "curb_concrete"),
                (0.0, ha, ap, top, "apron_sett"),
                (ap, top, ap, top + S.KERB_HEIGHT, "curb_concrete"),
                (ap, top + S.KERB_HEIGHT, ap + S.KERB_TOP_W, top + S.KERB_HEIGHT, "curb_concrete"),
                (ap + S.KERB_TOP_W, top + S.KERB_HEIGHT, ap + S.KERB_TOP_W, top + S.KERB_HEIGHT - depth,
                 "curb_concrete")]
    if kind == MEDIAN_RURAL:
        ps = S.PAVED_SHOULDER_MEDIAN
        z0 = -S.CROSSFALL * ps
        return [(0.0, 0.0, ps, z0, "road_asphalt"),
                (ps, z0, ps + 0.5, z0 - 0.03, "shoulder_gravel"),
                (ps + 0.5, z0 - 0.03, ps + 2.0, z0 - 0.12, "verge_grass"),
                (ps + 2.0, z0 - 0.12, ps + 2.0, z0 - 0.12 - depth, "verge_grass")]
    if kind == RURAL:
        ps = S.PAVED_SHOULDER
        zp = -S.CROSSFALL * ps
        sw = 0.75
        z1 = zp - S.SHOULDER_CROSSFALL * sw
        d = S.DITCH_DEPTH
        u0 = ps + sw
        u2 = u0 + d * S.DITCH_SLOPE
        u3 = u2 + S.DITCH_BOTTOM_W
        u4 = u3 + (d + z1) * S.DITCH_SLOPE
        return [(0.0, 0.0, ps, zp, "road_asphalt"),
                (ps, zp, u0, z1, "shoulder_gravel"),
                (u0, z1, u2, z1 - d, "verge_grass"),
                (u2, z1 - d, u3, z1 - d, "verge_grass"),
                (u3, z1 - d, u4, 0.0, "verge_grass"),
                (u4, 0.0, u4, -depth, "verge_grass")]
    tw = S.KERB_TOP_W
    zw = h + S.SIDEWALK_CROSSFALL * w
    return [(0.0, 0.0, 0.0, h, "curb_concrete"),
            (0.0, h, tw, h, "curb_concrete"),
            (tw, h, tw + w, zw, m if w > 0.05 else "curb_concrete"),
            (tw + w, zw, tw + w, zw - depth, m if w > 0.05 else "curb_concrete")]


def side_params(c: Chain, side: str, s: float) -> tuple:
    d = c.side[side]
    i = int(c.idx(s))
    return (int(d["kind"][i]), float(c.interp(d["h"], s)), float(c.interp(d["w"], s)),
            float(c.interp(d["depth"], s)), int(d["mat"][i]))


def side_extent(kind, h, w, depth, mat) -> float:
    return side_profile(kind, h, w, depth, mat)[-1][2]
