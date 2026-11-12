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
SURFACE_MAT = {"asphalt": "road_asphalt", "asphalt_new": "road_asphalt_new", "paved": "road_asphalt", "concrete": "road_concrete",
               "concrete:plates": "road_concrete", "paving_stones": "road_paving", "sett": "road_sett",
               "cobblestone": "road_sett", "unhewn_cobblestone": "road_sett", "compacted": "road_gravel",
               "gravel": "road_gravel", "fine_gravel": "road_gravel", "unpaved": "road_gravel",
               "ground": "road_gravel", "dirt": "road_gravel"}

# side profile families
URBAN, ISLAND, RURAL, MEDIAN_RURAL = 0, 1, 2, 3
WALK_MATS = ["curb_concrete", "sidewalk_paving", "bridge_concrete", "verge_grass", "road_asphalt"]
FLUSH_FILL_MAX_M = 1.5  # a flush edge strip is at most this wide (the flush mask is dilated 4 m past gap < NOSE_MIN_GAP_M)
MAT_FLUSH_ROAD = 4      # side `mat` code: flush edge shared with another carriageway -> asphalt, no kerb (ADR 0076)


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
    center_offset: float = 0.0  # authored: carriageway centre this far LEFT of the OSM way (edge direction), m (ADR 0077)
    # ADR 0095 (measured on the orthophoto, one-way carriageways only): distances from the LEFT carriageway edge in the
    # direction of travel to [start of lane 1, lane boundary 1|2, ..., end of the last lane]. lane_edges[0] is the
    # left edge strip / gutter; lanes need not be equal. In the override a last interval narrower than 2 m is the
    # right edge strip (shoulder beyond the right edge line): it sets `width`, not a lane.
    lane_edges: list | None = None
    center_offset_end: float | None = None   # authored: offset at the END of the edge (linear from center_offset)
    center_offset_profile: list | None = None  # authored: [[t, offset], ...], t = 0..1 along the edge (ADR 0095)
    width_profile: list | None = None          # authored: [[t, width], ...] along the edge (ADR 0095); `width` = max
    edge_lines: str | None = None   # painted edge lines in the direction of travel: none | left | right | both
    apron: str | None = None        # authored (ADR 0123): roundabout apron "asphalt" = no mountable sett apron, the ring
                                    # carriageway runs flush to the island kerb (orthophoto / photos); default sett apron
    provenance: dict = field(default_factory=dict)

    def lane_coord(self, lat, hw, dirn=1):
        """Lane coordinate across the carriageway (0 = first lane boundary, +1 per lane) for wheel-path weathering
        and paint UVs; follows the measured lane edges where they exist."""
        lat = np.asarray(lat, float)
        if self.lane_edges and self.oneway:
            x = np.asarray(hw, float) - (float(dirn) or 1.0) * lat
            le = np.asarray(self.lane_edges, float)
            return np.interp(x, le, np.arange(len(le), dtype=float))
        return (lat + np.asarray(hw, float) - self.edge_strip) / max(float(self.lane_w), 2.0)


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
            if "width" in st and isinstance(st["width"], (list, tuple)):
                # ADR 0095: measured width varying along the edge, [[t, w], ...] with t = 0..1 in the edge direction
                # (a ramp lane that widens beside a painted gore); lane layout keeps using the widest value
                sec.width_profile = sorted((float(t), float(v)) for t, v in st["width"])
                sec.width = max(v for _, v in sec.width_profile)
                sec.lane_w = round((sec.width - 2 * sec.edge_strip) / max(sec.lanes, 1), 3)
                sec.width_src = f"authored_override:{ov['id']} (profile)"
            elif "width" in st and "lane_edges" not in st:
                # measured carriageway width (orthophoto): lanes keep their count, lane width follows
                sec.width = float(st["width"])
                sec.lane_w = round((sec.width - 2 * sec.edge_strip) / max(sec.lanes, 1), 3)
                sec.width_src = f"authored_override:{ov['id']}"
            if "lane_edges" in st:
                # ADR 0095: lanes as measured on the orthophoto (count, widths and edge strip in one list)
                le = [float(v) for v in st["lane_edges"]]
                total = le[-1] if le else 0.0
                if len(le) >= 3 and 0 < le[-1] - le[-2] < 2.0:
                    le = le[:-1]                    # right edge strip
                if "width" in st and not isinstance(st["width"], (list, tuple)):
                    total = max(total, float(st["width"]))   # carriageway beyond the last lane (hatching, island)
                if not sec.oneway or len(le) < 2 or any(b - a < 2.0 for a, b in zip(le, le[1:])) or le[0] < 0:
                    if ov["id"] not in net.overrides_stale:
                        net.overrides_stale.append(ov["id"])
                    sec.provenance["lane_edges_rejected"] = le
                else:
                    sec.lane_edges = le
                    sec.lanes = sec.lanes_fwd = len(le) - 1
                    sec.edge_strip = le[0]
                    sec.width = total
                    sec.lane_w = round((le[-1] - le[0]) / sec.lanes, 3)
                    sec.width_src = f"authored_override:{ov['id']} (lane_edges, orthophoto)"
                    if "turn_lanes" not in st and sec.turn_fwd and len(sec.turn_fwd) != sec.lanes:
                        sec.turn_fwd = None
            if "edge_lines" in st:
                sec.edge_lines = str(st["edge_lines"])
            if "apron" in st:
                sec.apron = str(st["apron"])
            if "turn_lanes" in st:
                sec.turn_fwd = [t for t in str(st["turn_lanes"]).split("|")] if st["turn_lanes"] else None
            if "center_offset" in st:
                # the OSM way is not the carriageway centre here (like OSM placement=*): measured on the orthophoto
                co = st["center_offset"]
                if isinstance(co, (list, tuple)) and co and isinstance(co[0], (list, tuple)):
                    prof = sorted((float(t), float(v)) for t, v in co)   # ADR 0095: [[t, offset], ...] along the edge
                    sec.center_offset_profile = prof
                    sec.center_offset, sec.center_offset_end = prof[0][1], prof[-1][1]
                elif isinstance(co, (list, tuple)):     # ADR 0095: [at the start, at the end] of the edge, linear
                    sec.center_offset, sec.center_offset_end = float(co[0]), float(co[1])
                else:
                    sec.center_offset = float(co)
                sec.provenance["center_offset_m"] = co
            for side in ("left", "right"):
                if f"side_{side}" in st:
                    sec.side_override[side] = st[f"side_{side}"]
            if "surface" in st:
                sec.surface_mat = SURFACE_MAT.get(st["surface"], "road_asphalt")
                sec.provenance["surface_override"] = st["surface"]
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
    if any(s.center_offset or s.center_offset_end or s.center_offset_profile for s in secs):
        # authored lateral placement (ADR 0077): shift the carriageway centre off the OSM way, blended over 20 m
        L0 = c.raw_spans[-1][1]
        s0 = c.line.s * (L0 / max(c.line.length, 1e-9))
        k0 = np.clip(np.searchsorted([sp[1] for sp in c.raw_spans], s0, side="left"), 0, len(c.raw_spans) - 1)

        def _off(i, sr):
            a0, a1, eid, rv = c.raw_spans[i]
            sc = net.sections[eid]
            v0 = sc.center_offset
            v1 = v0 if sc.center_offset_end is None else sc.center_offset_end
            t = float(np.clip((sr - a0) / max(a1 - a0, 1e-6), 0.0, 1.0))
            if rv:
                t = 1.0 - t
            if sc.center_offset_profile:
                pr = sc.center_offset_profile
                return float(np.interp(t, [q[0] for q in pr], [q[1] for q in pr])) * (-1.0 if rv else 1.0)
            return (v0 + (v1 - v0) * t) * (-1.0 if rv else 1.0)
        off = np.array([_off(i, sr) for i, sr in zip(k0, s0)])
        if len(off) > 3 and np.ptp(off) > 0:
            # steps between per-edge constants are blended over ~20 m; a profile traced along the edge (ADR 0095)
            # is already continuous and may change fast (a link leaving the axis of the main carriageway)
            off = smooth_1d(off, (2.5 if any(s.center_offset_profile for s in secs) else 10.0) / DENSE)
        c.meta["center_offset"] = off
        c.line = Polyline(c.line.p + c.line.n * off[:, None])
    L_raw = c.raw_spans[-1][1]
    s_raw = c.line.s * (L_raw / max(c.line.length, 1e-9))
    k = np.searchsorted([sp[1] for sp in c.raw_spans], s_raw, side="left")
    k = np.clip(k, 0, len(c.raw_spans) - 1)
    c.sec_idx = np.array([sec_index[c.raw_spans[i][2]] for i in k])
    rev = np.array([c.raw_spans[i][3] for i in k])
    sl = net.sec_list
    hw = np.array([sl[i].width / 2 for i in c.sec_idx])
    for i_sp, (a0, a1, eid, rv) in enumerate(c.raw_spans):
        pr = net.sections[eid].width_profile
        if pr:
            m = k == i_sp
            t = np.clip((s_raw[m] - a0) / max(a1 - a0, 1e-6), 0.0, 1.0)
            hw[m] = np.interp(1.0 - t if rv else t, [q[0] for q in pr], [q[1] for q in pr]) / 2
    one = np.array([sl[i].oneway for i in c.sec_idx])
    c.dirn = np.where(one, np.where(rev, -1, 1), 0)
    c.bridge = np.array([sl[i].bridge for i in c.sec_idx])
    c.roundabout = bool(any(s.roundabout for s in secs))
    # width transitions: PTB2022 §17 ust.6 asks for smooth changes -> 15 m smoothing (WORKING_VALUE)
    c.hw = smooth_1d(hw, 7.5 / DENSE) if len(hw) > 3 else hw
    c.meta["rev"] = rev
    m = max(2, int(math.ceil(2 * float(c.hw.max()) / 1.75)))
    c.m_lat = m + (m % 2)          # even -> the crown (lat 0) is always a vertex


def taper_forks(net: Network, report: list | None = None):
    """At a node where two chains continue (nearly collinear, > FORK_STRAIGHT_DEG) with different
    carriageway widths, narrow the wider chain toward the other one's width over a taper of
    TAPER_RATIO x width difference (>= TAPER_MIN_M), so the junction patch sees equal edges and the kerb
    runs as a smooth skew instead of a Z-shaped step (PTB2022 §17 ust. 6: smooth width changes)."""
    ends = {}
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout or len(c.line.s) < 4:
            continue
        ends.setdefault(c.node_a, []).append((c, "a"))
        ends.setdefault(c.node_b, []).append((c, "b"))
    for node, lst in sorted(ends.items()):
        if len(lst) < 2:
            continue
        dirs = []
        for c, e in lst:
            s = min(6.0, c.length / 2) if e == "a" else c.length - min(6.0, c.length / 2)
            t, _ = c.line.frame(s)
            dirs.append(t if e == "a" else -t)
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                cosang = float(np.dot(dirs[i], dirs[j]))
                if cosang > -math.cos(math.radians(S.FORK_STRAIGHT_DEG)):
                    continue
                (ci, ei), (cj, ej) = lst[i], lst[j]
                hi_ = float(ci.hw[0] if ei == "a" else ci.hw[-1])
                hj_ = float(cj.hw[0] if ej == "a" else cj.hw[-1])
                if not (0.25 <= abs(hi_ - hj_) <= S.TAPER_MAX_DHW):
                    continue
                si = ci.section(min(1.0, ci.length) if ei == "a" else ci.length - 1.0, net.sec_list)
                sj = cj.section(min(1.0, cj.length) if ej == "a" else cj.length - 1.0, net.sec_list)
                if si.cls != sj.cls or si.oneway != sj.oneway or si.highway.endswith("_link") != sj.highway.endswith("_link"):
                    continue                     # a real diverge / merge, not one road changing width
                (cw, ew, hw_w), hn = ((ci, ei, hi_), hj_) if hi_ > hj_ else ((cj, ej, hj_), hi_)
                L = max(S.TAPER_MIN_M, S.TAPER_RATIO * (hw_w - hn) * 2)
                L = min(L, 0.6 * cw.length)
                d = cw.line.s if ew == "a" else cw.length - cw.line.s
                f = np.clip(d / L, 0, 1)
                f = f * f * (3 - 2 * f)
                target = hn + (cw.hw - hn) * f
                cw.hw = np.where(d < L, np.minimum(cw.hw, target), cw.hw)
                if report is not None:
                    report.append({"node": node, "chain": cw.id, "from_hw": round(hw_w, 2), "to_hw": round(hn, 2),
                                   "taper_m": round(L, 1)})


FORK_ALIGN_MAX_DEG = 60.0      # branches of a diverge / merge within this angle of the main carriageway
FORK_ALIGN_MIN_M = 40.0        # lateral shift taper: max(this, FORK_ALIGN_RATIO x shift) (WORKING_VALUE)
FORK_ALIGN_RATIO = 20.0
FORK_GORE_CLEAR_M = 1.0       # hold the shift until the branch edges are this far apart (WORKING_VALUE, ADR 0074)
FORK_HOLD_MAX_M = 40.0        # ... but never longer (parallel carriageways of a long viaduct never "separate")


def align_forks(net: Network, report: list | None = None):
    """Lane continuity at diverges and merges of one-way carriageways (ADR 0074).

    OSM draws every carriageway on its own centre line and splits them in one node, so a 3-lane carriageway that
    diverges into a 2-lane viaduct and a 1-lane link (Andersa before Rondo Putry) had the viaduct centred under its
    middle lane: the left lane ran into the viaduct's kerb. Here the lanes of the single carriageway are dealt out
    left to right to the branches ordered left to right (each branch takes as many lanes as it has), and every
    branch centre line is shifted sideways at the node so its lanes lie under the lanes it takes, the shift fading
    out with a smoothstep over max(FORK_ALIGN_MIN_M, FORK_ALIGN_RATIO x shift). Applies only when the branch lane
    counts add up to the single carriageway's lanes (otherwise it is a lane gain / drop the data must describe)."""
    from .markings import lane_layout
    ends = {}
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout or c.closed or len(c.line.s) < 8:
            continue
        ends.setdefault(c.node_a, []).append((c, "a"))
        ends.setdefault(c.node_b, []).append((c, "b"))
    secs = net.sec_list
    for node, lst in sorted(ends.items(), key=lambda kv: kv[0]):
        if len(lst) < 3:
            continue
        info = []
        for c, e in lst:
            s_in = min(1.0, c.length / 2) if e == "a" else c.length - min(1.0, c.length / 2)
            sec = c.section(s_in, secs)
            if not sec.oneway:
                break
            dn = int(c.dirn[c.idx(s_in)]) or 1
            outward = (dn > 0) == (e == "a")          # traffic leaves the node along this chain
            s15 = min(15.0, c.length * 0.5) if e == "a" else c.length - min(15.0, c.length * 0.5)
            p0 = c.line.point(0.0 if e == "a" else c.length)
            v = c.line.point(s15) - p0
            v = v / max(float(np.hypot(*v)), 1e-9)
            info.append((c, e, sec, dn, outward, v))
        else:
            outs = [x for x in info if x[4]]
            ins = [x for x in info if not x[4]]
            for single, branches in ((ins, outs), (outs, ins)):
                if len(single) != 1 or len(branches) < 2:
                    continue
                sc, se, ssec, sdn, sout, sv = single[0]
                travel = -sv if not sout else sv          # direction of travel of the single carriageway at the node
                away = -travel if sout else travel        # where the branches lie: ahead (diverge) / behind (merge)
                s_node = 0.0 if se == "a" else sc.length
                _, n_s0 = sc.line.frame(s_node)
                nl0 = n_s0 * (1.0 if sdn > 0 else -1.0)  # travel-left normal of the single carriageway
                br = []
                ok = True
                for c, e, sec, dn, outw, v in branches:
                    ang = math.degrees(math.atan2(away[0] * v[1] - away[1] * v[0], float(np.dot(away, v))))
                    if abs(ang) > FORK_ALIGN_MAX_DEG:
                        ok = False
                    br.append((float(np.dot(v, nl0)), c, e, sec, dn))
                if not ok or sum(b[3].lanes for b in br) != ssec.lanes:
                    continue
                br.sort(key=lambda b: -b[0])              # left to right in the direction of travel
                hw_s = float(sc.hw_at(s_node))
                _, _, cen = lane_layout(ssec, hw_s, sdn)
                lanes_s = cen["fwd"]                      # left -> right in travel direction, chain lateral
                # chain lateral -> travel-left lateral of the single carriageway
                tl_sign = 1.0 if sdn > 0 else -1.0
                k0 = 0
                for ang, c, e, sec, dn in br:
                    take = [lanes_s[i] * tl_sign for i in range(k0, k0 + sec.lanes)]
                    k0 += sec.lanes
                    s_b = 0.0 if e == "a" else c.length
                    hw_b = float(c.hw_at(s_b))
                    _, _, cb = lane_layout(sec, hw_b, dn)
                    bl = [x * (1.0 if dn > 0 else -1.0) for x in cb["fwd"]]   # travel-left lateral in the branch
                    p_s = sc.line.point(s_node)
                    p_b = c.line.point(s_b)
                    t_s, n_s = sc.line.frame(s_node)
                    nl = n_s * tl_sign                    # travel-left normal of the single carriageway
                    want = float(np.mean(take)) - float(np.mean(bl))   # branch centre lateral it should have
                    have = float(np.dot(p_b - p_s, nl))
                    shift = want - have                   # + = towards travel-left
                    if abs(shift) < 0.3:
                        continue
                    if getattr(sec, "center_offset_profile", None):
                        continue        # ADR 0095: placement traced along the edge on the orthophoto is absolute
                    # hold the full shift until the branch has left its neighbours (gore), then fade it out
                    d = c.line.s if e == "a" else c.length - c.line.s
                    others = [LineString(o.line.p) for _, o, _, _, _ in br if o is not c]
                    oh = max([float(np.max(o.hw)) for _, o, _, _, _ in br if o is not c] or [0.0])
                    hold = 0.0
                    for dd in np.arange(0.0, 0.6 * c.length, 2.0):
                        q = c.line.point(dd if e == "a" else c.length - dd)
                        hb = float(c.hw_at(dd if e == "a" else c.length - dd))
                        clear = min(Point(q).distance(o) for o in others) if others else 1e9
                        if clear - abs(shift) > hb + oh + FORK_GORE_CLEAR_M:  # gore fully open (past the kerb returns)
                            break
                        hold = min(dd, FORK_HOLD_MAX_M)
                    L = max(FORK_ALIGN_MIN_M, FORK_ALIGN_RATIO * abs(shift))
                    L = min(L, max(0.8 * c.length - hold, 5.0))
                    f = np.clip(1.0 - (d - hold) / L, 0.0, 1.0)
                    f = f * f * (3 - 2 * f)
                    # branch travel-left normal along the branch = chain normal * branch travel sign
                    nb = c.line.n * (1.0 if dn > 0 else -1.0)
                    pts = c.line.p + nb * (shift * f)[:, None]
                    c.line = Polyline(pts)
                    c.meta["fork_shift_m"] = round(shift, 2)
                    if report is not None:
                        report.append({"node": node, "chain": c.id, "shift_m": round(shift, 2), "hold_m": round(float(hold), 1), "taper_m": round(L, 1),
                                       "lanes": [round(x, 2) for x in take]})


# Lateral push of merging / diverging carriageways (ADR 0076 r1) is OFF: checked against the GUGiK orthophoto
# (artifacts/roads-p0-r10/abreast_ortho/*.jpg, abreast_vs_ortho.json) the pushed layout put 4006 m2 more asphalt
# into the 8 node windows, 147 m2 more of it on vegetation (Andersa west: carriageway edges 5-9 m out on the verge
# and the footway) and moved the start-route axis up to 6.9 m off OSM (p95 1.745 m, ratchet 0.13 m). The real merge
# lanes lie where OSM draws them: the carriageways overlap and are one surface. With the push off abreast_forks
# only records which carriageway each overlapping branch lies on (meta "abreast_of"), so profile.build_profiles
# (step 1b) puts both on one surface; kerbs inside the overlap are removed by meshing.cull_sides_on_carriageway.
ABREAST_PUSH = False
ABREAST_OVERLAP_M = 0.3       # carriageways laid side by side overlap by this much (one surface, no sliver; WORKING_VALUE)
ABREAST_SMOOTH_M = 5.0        # Gaussian sigma of the lateral push along the chain (WORKING_VALUE)
ABREAST_RELEASE_M = 15.0      # the push ends once the carriageways have been clear of each other this long
ABREAST_NODE_FADE_M = 30.0    # a displaced node drags its other chains with it over this length (WORKING_VALUE)
ABREAST_MIN_RUN_M = 12.0      # carriageways overlapping for less than this are a plain Y junction (patch + fillets)
ABREAST_SKIP_HIGHWAYS = ("service", "residential", "living_street", "unclassified", "track")
ABREAST_TAPER_RATIO = 12.0    # lane-drop / lane-gain taper of the single carriageway: ratio x extra width (WORKING_VALUE)


def _smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def _reline(c: Chain, pts: np.ndarray):
    """Replace the chain's centre line and resample it (and the per-station arrays) to DENSE spacing again: a
    lateral displacement that varies along the chain stretches the samples, and Chain.idx assumes s = i * DENSE."""
    s_old = cumlen(pts)
    L = float(s_old[-1])
    n = max(2, int(round(L / DENSE)) + 1)
    t = np.linspace(0.0, L, n)
    q = np.column_stack([np.interp(t, s_old, pts[:, 0]), np.interp(t, s_old, pts[:, 1])])
    j = np.clip(np.searchsorted(s_old, t, side="left"), 0, len(s_old) - 1)
    c.hw = np.interp(t, s_old, c.hw)
    c.sec_idx, c.dirn, c.bridge = c.sec_idx[j], c.dirn[j], c.bridge[j]
    c.meta["rev"] = c.meta["rev"][j]
    c.line = Polyline(q)


def _end_dir(c: Chain, e: str, d: float = 15.0):
    """Unit vector from the chain end `e` along the chain (chord over d m)."""
    d = min(d, c.length * 0.5)
    p0 = c.line.point(0.0 if e == "a" else c.length)
    v = c.line.point(d if e == "a" else c.length - d) - p0
    return v / max(float(np.hypot(*v)), 1e-9)


def _leaves(c: Chain, e: str) -> bool:
    """Traffic leaves the node at end `e` along this (one-way) chain."""
    s_in = min(1.0, c.length / 2) if e == "a" else c.length - min(1.0, c.length / 2)
    dn = int(c.dirn[c.idx(s_in)]) or 1
    return (dn > 0) == (e == "a")


def _push_abreast(net: Network, ends: dict, c: Chain, e: str, nb: Chain, side: float, report: list, node: str,
                  visited: set, floor: float = 0.0):
    """Push chain c (from its end `e` outward) sideways until its carriageway no longer overlaps the roughly
    parallel carriageway nb by more than ABREAST_OVERLAP_M. side = +1: c lies to the travel-left of nb, -1: right.
    Where the OSM axes are further apart than the two half widths nothing moves, so the carriageways separate
    exactly where OSM separates them. If c ends (far node) while still pushed, that node is displaced: the chain
    that continues the same traffic stream is pushed on, every other chain there is dragged along (fading)."""
    n = len(c.line.s)
    order = np.arange(n) if e == "a" else np.arange(n)[::-1]
    deficit = np.zeros(n)
    clear_run = 0.0
    nb_end = (nb.line.p[0], -nb.line.t[0]), (nb.line.p[-1], nb.line.t[-1])
    for i in order:
        q = c.line.p[i]
        s_o, lat = nb.line.project(q)
        ok = True
        if s_o <= 1e-6 or s_o >= nb.length - 1e-6:           # beyond the neighbour's end: only right at the node
            pe, te = nb_end[0] if s_o <= 1e-6 else nb_end[1]
            ok = float(np.dot(q - pe, te)) <= 1.0
        io = nb.idx(s_o)
        if ok and abs(float(np.dot(nb.line.t[io], c.line.t[i]))) < 0.7:
            ok = False
        # a deck over / beside a ground road is not "abreast": only carriageways on the same level
        # (OSM `layer` alone is no level: an embankment ramp is layer 1 down to the node where it meets the link)
        if ok and bool(nb.bridge[io]) != bool(c.bridge[i]):
            ok = False
        need = 0.0
        if ok:
            dn_nb = int(nb.dirn[io]) or 1
            need = float(c.hw[i]) + float(nb.hw_at(s_o)) - ABREAST_OVERLAP_M - side * dn_nb * lat
        if need > 0.0:
            deficit[i] = need
            clear_run = 0.0
        else:
            clear_run += DENSE
            if clear_run >= ABREAST_RELEASE_M:
                break
    d = c.line.s if e == "a" else c.length - c.line.s
    far = -1 if e == "a" else 0
    far_node = c.node_b if e == "a" else c.node_a
    if floor <= 0.0 and float((deficit > 0).sum()) * DENSE < min(ABREAST_MIN_RUN_M, 0.9 * c.length):
        return
    if not ABREAST_PUSH:                                     # axes stay on OSM: one surface, no lateral move
        c.meta["abreast_of"] = nb.id
        c.meta["abreast_overlap_m"] = round(float((deficit > 0).sum()) * DENSE, 1)
        report.append({"node": node, "chain": c.id, "beside": nb.id, "side": "left" if side > 0 else "right",
                       "overlap_run_m": c.meta["abreast_overlap_m"], "overlap_max_m": round(float(deficit.max()), 2),
                       "shift_max_m": 0.0})
        return
    final = smooth_1d(deficit, ABREAST_SMOOTH_M / DENSE) if n > 3 else deficit
    if floor > 0.0:
        final = np.maximum(final, floor * _smoothstep(1.0 - d / ABREAST_NODE_FADE_M))
    resid = float(final[far])
    others = [(o, oe) for o, oe in ends.get(far_node, []) if o is not c]
    can_move_node = resid > 0.3 and all(not o.roundabout and not o.closed and o.id not in visited for o, _ in others)
    if resid > 0.3 and not can_move_node:                    # the far node stays: fade the push out before it
        final = final * _smoothstep((c.length - d) / min(15.0, 0.5 * c.length))
        resid = 0.0
    if float(final.max()) < 0.05:
        return
    s_in = min(1.0, c.length / 2) if e == "a" else c.length - min(1.0, c.length / 2)
    dn_c = int(c.dirn[c.idx(s_in)]) or 1
    vec = c.line.n * (side * dn_c) * final[:, None]
    delta = vec[far].copy()
    v_far = -_end_dir(c, "b" if e == "a" else "a")           # direction of c arriving at the far node (from `node`)
    leaves_far = _leaves(c, "b" if e == "a" else "a")
    _reline(c, c.line.p + vec)
    c.meta["abreast_of"] = nb.id
    c.meta["abreast_shift_m"] = round(float(final.max()), 2)
    report.append({"node": node, "chain": c.id, "beside": nb.id, "side": "left" if side > 0 else "right",
                   "shift_max_m": round(float(final.max()), 2), "pushed_m": round(float((final > 0.05).sum() * DENSE), 1),
                   "far_node_moved_m": round(resid, 2)})
    if resid <= 0.3:
        return
    for o, oe in others:
        visited.add(o.id)
        cont = bool((o.dirn != 0).all()) and _leaves(o, oe) != leaves_far and float(np.dot(_end_dir(o, oe), v_far)) > 0.77
        if cont:
            _push_abreast(net, ends, o, oe, nb, side, report, far_node, visited, floor=resid)
        else:
            do = o.line.s if oe == "a" else o.length - o.line.s
            f = _smoothstep(1.0 - do / min(ABREAST_NODE_FADE_M, 0.8 * o.length))
            _reline(o, o.line.p + delta[None, :] * f[:, None])
            report.append({"node": far_node, "chain": o.id, "dragged_m": round(float(np.hypot(*delta)), 2)})


ALONGSIDE_GAP_M = 1.0        # WORKING_VALUE: edges closer than this = one surface (painted separation at most)
ALONGSIDE_MIN_RUN_M = 15.0   # WORKING_VALUE


def _tie_alongside(c: Chain, e: str, nb: Chain, report: list, node: str):
    """Mark chain c (leaving `node` at end e) as sharing nb's height surface when their edges run within
    ALONGSIDE_GAP_M of each other for at least ALONGSIDE_MIN_RUN_M (no lateral move)."""
    if c.meta.get("abreast_of"):
        return
    idx = range(len(c.line.s)) if e == "a" else range(len(c.line.s) - 1, -1, -1)
    run, far = 0.0, 0.0
    for i in idx:
        d = float(c.line.s[i]) if e == "a" else float(c.length - c.line.s[i])
        if d > 250.0:
            break
        s_o, lat = nb.line.project(c.line.p[i])
        if s_o <= 1e-6 or s_o >= nb.length - 1e-6:
            continue
        io = nb.idx(s_o)
        if abs(float(np.dot(nb.line.t[io], c.line.t[i]))) < 0.7 or bool(nb.bridge[io]) != bool(c.bridge[i]):
            continue
        if abs(lat) - float(c.hw[i]) - float(nb.hw_at(s_o)) < ALONGSIDE_GAP_M:
            run += DENSE
            far = d
    if run >= ALONGSIDE_MIN_RUN_M:
        c.meta["abreast_of"] = nb.id
        c.meta["alongside_m"] = round(run, 1)
        report.append({"node": node, "chain": c.id, "beside": nb.id, "alongside_run_m": round(run, 1),
                       "to_m": round(far, 1), "shift_max_m": 0.0})


def abreast_forks(net: Network, report: list | None = None):
    """Merges and diverges of one-way carriageways whose lanes do NOT add up (a lane gain / drop at the node: an
    on-ramp joining a carriageway that keeps its lane count, ADR 0076; align_forks handles the ones that add up).

    OSM draws the ramp axis into the axis of the main carriageway, so the two generated carriageways overlapped
    for 15-45 m before the node: each kept its own kerb, verge and height profile there -> a kerb along and across
    the lanes (MA-001 / MA-002, Andersa on-ramp from Rondo Biezenstwa), a 45 m junction patch stretched between two
    profiles 1.9 m apart (MA-012, on-ramp from Rondo Putry). Here the branches are laid side by side at the node:
    the branch that continues the single carriageway keeps its edge on the single carriageway's edge, the others
    are pushed outward just enough not to overlap their inner neighbour (_push_abreast), and the single
    carriageway is widened at the node to take them all, tapering back over ABREAST_TAPER_RATIO x the extra width
    (the merge / diverge lane).

    r2 (ABREAST_PUSH = False, see there): nothing is moved or widened any more - the orthophoto shows the OSM axes
    are the truer layout. The overlapping branch is only tied to its inner neighbour (meta "abreast_of") so that
    both get one height surface (profile step 1b)."""
    report = [] if report is None else report
    ends = {}
    for c in net.chains:
        if c.meta.get("absorbed") or c.closed or len(c.line.s) < 8:
            continue
        ends.setdefault(c.node_a, []).append((c, "a"))
        ends.setdefault(c.node_b, []).append((c, "b"))
    secs = net.sec_list
    for node, lst in sorted(ends.items(), key=lambda kv: kv[0]):
        if len(lst) < 3 or any(c.roundabout or not bool((c.dirn != 0).all()) for c, _ in lst):
            continue
        outs = [(c, e) for c, e in lst if _leaves(c, e)]
        ins = [(c, e) for c, e in lst if not _leaves(c, e)]
        for single, branches in ((ins, outs), (outs, ins)):
            if len(single) != 1 or len(branches) < 2:
                continue
            sc, se = single[0]
            s_node = 0.0 if se == "a" else sc.length
            s_in = min(1.0, sc.length / 2) if se == "a" else sc.length - min(1.0, sc.length / 2)
            ssec = sc.section(s_in, secs)
            sdn = int(sc.dirn[sc.idx(s_in)]) or 1
            sv = _end_dir(sc, se)
            away = -sv                                   # where the branches lie, seen from the node
            _, n_s0 = sc.line.frame(s_node)
            nl0 = n_s0 * float(sdn)                      # travel-left normal of the single carriageway
            br = []
            for c, e in branches:
                v = _end_dir(c, e)
                ang = math.degrees(math.atan2(away[0] * v[1] - away[1] * v[0], float(np.dot(away, v))))
                sec = c.section(min(1.0, c.length / 2) if e == "a" else c.length - min(1.0, c.length / 2), secs)
                br.append({"c": c, "e": e, "ang": ang, "lat": float(np.dot(v, nl0)), "sec": sec,
                           "hw": float(c.hw_at(0.0 if e == "a" else c.length))})
            if any(abs(b["ang"]) > FORK_ALIGN_MAX_DEG for b in br):
                continue
            if sum(b["sec"].lanes for b in br) <= ssec.lanes:
                # lanes add up (align_forks) or fewer: nothing to lay out. ADR 0095: a branch that then runs edge to
                # edge with its neighbour (a ramp lane beside the main carriageway up to a painted gore) still
                # shares that neighbour's height surface - tie it like an overlapping branch.
                br.sort(key=lambda b: -b["lat"])
                ia = min(range(len(br)), key=lambda i: (abs(br[i]["ang"]), -br[i]["sec"].lanes))
                for i in range(len(br)):
                    if i != ia:
                        _tie_alongside(br[i]["c"], br[i]["e"], br[i + 1]["c"] if i < ia else br[i - 1]["c"], report, node)
                continue
            if ssec.highway in ABREAST_SKIP_HIGHWAYS:
                continue                                 # yard lanes / side streets: a Y junction, not a merge lane
            br.sort(key=lambda b: -b["lat"])             # left -> right in the direction of travel
            ia = min(range(len(br)), key=lambda i: (abs(br[i]["ang"]), -br[i]["sec"].lanes))
            hw_s = float(sc.hw_at(s_node))
            p_s = sc.line.point(s_node)
            # the continuing branch stays on its OSM axis; the others are laid beside it
            visited = {sc.id} | {b["c"].id for b in br}
            n_rep = len(report)
            for i in list(range(ia - 1, -1, -1)) + list(range(ia + 1, len(br))):
                b = br[i]
                nb = br[i + 1]["c"] if i < ia else br[i - 1]["c"]
                _push_abreast(net, ends, b["c"], b["e"], nb, 1.0 if i < ia else -1.0, report, node, visited)
            if len(report) == n_rep or not ABREAST_PUSH:
                continue                                 # nothing overlapped (a plain Y junction) / nothing moved
            # widen the single carriageway at the node to the laid-out branches, taper back (merge / diverge lane)
            lats = []
            for b in br:
                c, e = b["c"], b["e"]
                s_b = 0.0 if e == "a" else c.length
                cen = float(np.dot(c.line.point(s_b) - p_s, nl0))
                hb = float(c.hw_at(s_b))
                lats += [cen + hb, cen - hb]
            e_l, e_r = max(0.0, max(lats) - hw_s), max(0.0, -hw_s - min(lats))
            if e_l + e_r >= 0.3:
                d = sc.line.s if se == "a" else sc.length - sc.line.s
                L = min(max(FORK_ALIGN_MIN_M, ABREAST_TAPER_RATIO * (e_l + e_r)), 0.8 * sc.length)
                f = _smoothstep(1.0 - d / L)
                sc.hw = sc.hw + 0.5 * (e_l + e_r) * f
                _reline(sc, sc.line.p + sc.line.n * float(sdn) * (0.5 * (e_l - e_r) * f)[:, None])
                m = max(2, int(math.ceil(2 * float(sc.hw.max()) / 1.75)))
                sc.m_lat = max(sc.m_lat, m + (m % 2))
                sc.meta["abreast_widen_m"] = round(e_l + e_r, 2)
                report.append({"node": node, "chain": sc.id, "widen_left_m": round(e_l, 2), "widen_right_m": round(e_r, 2),
                               "taper_m": round(L, 1)})
    return report


# --------------------------------------------------------------------------------------------
def assign_sides(net: Network, footways: list, built_up: bool = True, walkways: list | None = None,
                 yards=None, trims: bool = False):
    """Per-station side profile parameters for every chain (left 'L' and right 'R' of chain direction)."""
    # one-way carriageways (for median detection)
    ow_lines, ow_meta = [], []
    for c in net.chains:
        if (c.dirn != 0).all():
            ow_lines.append(LineString(c.line.p))
            ow_meta.append(c)
    ow_tree = shapely.STRtree(ow_lines) if ow_lines else None
    all_chains = list(net.chains)
    all_tree = shapely.STRtree([LineString(c.line.p) for c in all_chains])
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
        # A footway / cycle path set back from the carriageway (within RURAL_FOOT_M, e.g. the cycle path
        # along DK8) no longer turns the edge into an urban kerb: at >= 70 km/h the edge stays without a
        # kerb (paved shoulder + verge, PTB2022 § 23 ust. 10) and only the ditch becomes a shallow swale
        # (SWALE_DEPTH) so the profile ends before the path. Only a sidewalk attached to the kerb (walk_d
        # below) keeps the urban kerbed edge.
        rural_d = {"L": np.zeros(n, bool), "R": np.zeros(n, bool)}
        path_d = {"L": np.zeros(n, bool), "R": np.zeros(n, bool)}
        if fast:
            win = max(1, int(round(30.0 / 4.0)))
            for side_, sg in (("L", 1.0), ("R", -1.0)):
                hits = np.zeros(len(idx))
                for j, i in enumerate(idx):
                    q = Point(*(c.line.p[i] + c.line.n[i] * sg * (c.hw[i] + S.RURAL_FOOT_M / 2)))
                    hits[j] = 1.0 if len(wk_tree.query(q.buffer(S.RURAL_FOOT_M / 2 + 1.0))) else 0.0
                hs = np.array([hits[max(0, j - win):j + win + 1].mean() for j in range(len(idx))]) >= 0.2
                path_d[side_] = np.interp(np.arange(n), idx, hs.astype(float)) > 0.5
                rural_d[side_] = np.ones(n, bool)
        c.meta["rural"] = {k: round(float(v.mean()), 2) for k, v in rural_d.items()}
        c.meta["rural_path"] = {k: round(float(v.mean()), 2) for k, v in path_d.items()}
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
            rural_here = rural_d[side] & ~(walk_d & ~med_d)
            kind = np.where(rural_here | (not built_up), RURAL, URBAN)
            h = np.full(n, S.KERB_HEIGHT)
            h[rural_here] = np.where(path_d[side][rural_here], S.SWALE_DEPTH, S.DITCH_DEPTH)    # RURAL: h = ditch depth
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
            os_ = "L" if side == "R" else "R"
            other = rural_d[os_] & ~path_d[os_]          # median rule unchanged: other side free of paths
            fast_med = fast and (sec_mid.maxspeed or 50) >= 90
            kind[med_d] = np.where(other[med_d] | fast_med, MEDIAN_RURAL, URBAN)
            # ADR 0100 (REVIEW s10-0095 P1-7): a rural station turned into a kerbed URBAN median kept the DITCH depth
            # as its kerb height (h = 0.60): 0.6 m concrete "walls" along the DK8 median E -888...-768 and others
            h[(kind == URBAN) & rural_here] = S.KERB_HEIGHT
            if c.roundabout and side == ("L" if (c.dirn > 0).mean() >= 0.5 else "R"):
                kind[:] = ISLAND
                w[:] = S.ROUNDABOUT_APRON_W
                # ADR 0123 (REVIEW s11 D51 blocker 7): `apron: asphalt` on the ring edges = the 2 m strip is carriageway
                # (asphalt, no 4 cm lip); the island kerb, the footprint and the lane layout stay
                mat[:] = MAT_FLUSH_ROAD if sec_mid.apron == "asphalt" else 0
            # a parallel carriageway right next to this edge (on-ramp beside the Andersa ramp at Rondo Bieżeństwa):
            # the verge / ditch / sidewalk would lie on the other road, so the edge is a plain kerb
            if not (c.roundabout and kind[0] == ISLAND):
                tight, flush, gap = _tight_side(c, sgn, idx, kind, h, w, depth, mat, all_tree, all_chains, trims)
                kind[tight], h[tight], w[tight], mat[tight] = URBAN, S.KERB_HEIGHT, 0.0, 0
                h[flush] = 0.0                    # the other carriageway touches / overlaps: no kerb ridge in it
                mat[flush] = MAT_FLUSH_ROAD
                # ... and the flush asphalt strip reaches the other carriageway: the 0.15 m strips of the two edges
                # left a 0.3-0.9 m slot down to the terrain where the gap opens (j:n10015785253, terrain_walls QA)
                w[flush] = np.clip(gap[flush], 0.0, FLUSH_FILL_MAX_M)
                c.meta.setdefault("tight_m", {})[side] = round(float(tight.sum() * DENSE), 1)
                c.meta.setdefault("flush_m", {})[side] = round(float(flush.sum() * DENSE), 1)
            # ADR 0110 (REVIEW s10-0100 P1-1): grass behind a kerb that has no sidewalk, at the kerb crown. The kerb
            # used to end in its 0.5 m buried flange and the 1 m terrain grid lay 0.03-0.4 m lower behind it: from the
            # other carriageway the flange read as a concrete wall and every median as a trough. Width: VERGE_W, in a
            # median up to MEDIAN_VERGE_MAX, never past the middle of the gap to a parallel carriageway.
            gapm = _side_gap(c, sgn, idx, all_tree, all_chains, trims)
            verge = np.where(med_d, S.MEDIAN_VERGE_MAX, S.VERGE_W)
            verge = np.minimum(verge, np.maximum((gapm - 2 * S.KERB_TOP_W) / 2, 0.0))
            verge[(kind != URBAN) | (w > 0.05) | (mat != 0) | (h < 0.05) | c.bridge] = 0.0
            # the width changes by at most 1 m per 2 m along the kerb (median flag / gap steps: 1 m -> 3 m between two
            # stations gave 0.6 m grass faces in the skirt, terrain_walls b2)
            dv = 0.5 * np.diff(c.line.s)
            for i in range(1, n):
                verge[i] = min(verge[i], verge[i - 1] + dv[i - 1])
            for i in range(n - 2, -1, -1):
                verge[i] = min(verge[i], verge[i + 1] + dv[i])
            c.side[side] = {"kind": kind, "walk": walk_d, "median": med_d, "raw": {"h": h, "w": w, "depth": depth},
                            "mat": mat, "verge": verge}
        structure_sides(c, c.bridge)


def _tight_side(c, sgn, idx, kind, h, w, depth, mat, tree, chains, trims=False):
    """Stations whose side profile (verge, ditch, sidewalk) would reach onto another, roughly parallel carriageway:
    gap between this edge and the other edge < profile extent + 0.3 m (and gap < NOSE_MIN_GAP_M: touching or
    overlapping, returned as the second mask -> flush edge; third = that gap per station, held from the nearest
    station that has such a carriageway). Chains meeting this one at a node are ignored
    within ADJ_NODE_SKIP_M of it (junction patches join them). Checked every 4 m, dilated by 4 m."""
    n = len(c.line.s)
    hit = np.zeros(len(idx), bool)
    touch = np.zeros(len(idx), bool)
    gapv = np.zeros(len(idx))
    nodes = {c.node_a: 0.0, c.node_b: c.length}
    # chains sharing a node: skipped where the junction patch joins them. Before the junctions exist that is a
    # guess (ADJ_NODE_SKIP_M); the second assign_sides pass (trims=True) knows the trims, so a verge / kerb of one
    # branch no longer lies on the other branch's lane between the patch and 30 m (ADR 0076).
    skip = {c.node_a: (c.t_a + 1.0) if trims else S.ADJ_NODE_SKIP_M, c.node_b: (c.t_b + 1.0) if trims else S.ADJ_NODE_SKIP_M}
    for j, i in enumerate(idx):
        p, nrm, t = c.line.p[i], c.line.n[i] * sgn, c.line.t[i]
        ext = side_extent(int(kind[i]), float(h[i]), float(w[i]), float(depth[i]), int(mat[i]))
        e = p + nrm * c.hw[i]
        for k in tree.query(Point(*(e + nrm * ext * 0.5)).buffer(ext * 0.5 + 0.3 + 6.0)):
            oc = chains[int(k)]
            if oc is c:
                continue
            if any(abs(c.line.s[i] - nodes[nd]) < skip[nd] for nd in {oc.node_a, oc.node_b} & set(nodes)):
                continue
            s_o, lat_o = oc.line.project(e)
            if s_o <= 0.0 or s_o >= oc.length:
                continue
            io = oc.idx(s_o)
            if abs(float(np.dot(oc.line.t[io], t))) < 0.9:
                continue
            if float(np.dot(oc.line.point(s_o) - p, nrm)) <= 0.0:       # other road on the far side
                continue
            gap = abs(lat_o) - oc.hw_at(s_o)
            if gap < ext + 0.3:
                hit[j] = True
                gapv[j] = max(float(gap), 0.0)
                if gap < S.NOSE_MIN_GAP_M:
                    touch[j] = True
                break
    win = 1
    hs = np.array([hit[max(0, j - win):j + win + 1].any() for j in range(len(idx))])
    ts = np.array([touch[max(0, j - win):j + win + 1].any() for j in range(len(idx))])
    return (np.interp(np.arange(n), idx, hs.astype(float)) > 0.0,
            np.interp(np.arange(n), idx, ts.astype(float)) > 0.0,
            np.interp(np.arange(n), np.asarray(idx)[hit], gapv[hit]) if hit.any() else np.zeros(n))


def _side_gap(c, sgn, idx, tree, chains, trims=False, reach=2 * 3.0 + 1.0):
    """Clear distance [m] per dense station from this edge (gutter) to the gutter of the nearest roughly parallel
    carriageway lying on this side within `reach` (inf where there is none); checked at `idx`, the minimum of the
    neighbouring checks is held in between (ADR 0110, as _tight_side without the profile-extent test)."""
    n = len(c.line.s)
    gapv = np.full(len(idx), np.inf)
    nodes = {c.node_a: 0.0, c.node_b: c.length}
    skip = {c.node_a: (c.t_a + 1.0) if trims else S.ADJ_NODE_SKIP_M, c.node_b: (c.t_b + 1.0) if trims else S.ADJ_NODE_SKIP_M}
    for j, i in enumerate(idx):
        p, nrm, t = c.line.p[i], c.line.n[i] * sgn, c.line.t[i]
        e = p + nrm * c.hw[i]
        for k in tree.query(Point(*(e + nrm * reach * 0.5)).buffer(reach * 0.5 + 6.0)):
            oc = chains[int(k)]
            if oc is c or oc.meta.get("absorbed"):
                continue
            if any(abs(c.line.s[i] - nodes[nd]) < skip[nd] for nd in {oc.node_a, oc.node_b} & set(nodes)):
                continue
            s_o, lat_o = oc.line.project(e)
            if s_o <= 0.0 or s_o >= oc.length:
                continue
            io = oc.idx(s_o)
            if abs(float(np.dot(oc.line.t[io], t))) < 0.7:
                continue
            if float(np.dot(oc.line.point(s_o) - p, nrm)) <= 0.0:       # other road on the far side
                continue
            gapv[j] = min(gapv[j], max(float(abs(lat_o) - oc.hw_at(s_o)), 0.0))
    g = np.array([gapv[max(0, j - 1):j + 2].min() for j in range(len(idx))])
    out = np.full(n, np.inf)
    ia = np.asarray(idx)
    for a, b, ga, gb in zip(ia[:-1], ia[1:], g[:-1], g[1:]):
        out[a:b + 1] = np.minimum(out[a:b + 1], min(ga, gb))
    return out


def structure_sides(c: Chain, mask: np.ndarray):
    """Side profile of deck stations (bridges, and walled ramps once profile.mark_walled_ramps found them):
    kerb 0.20 + cap 1.50 + fascia = deck thickness, then the per-station values are smoothed (2 m). v3.1 marked
    walled ramps after assign_sides, so they kept the rural shoulder + ditch at deck height (a 2.65 m strip
    instead of the 1.5 m cap, overhanging the on-ramp beside Andersa at Rondo Bieżeństwa)."""
    sig = 2.0 / DENSE
    from . import meshing as _M              # bridge_style overrides (ADR 0117: per-bridge cap width `cap_w`)
    cap_w = _M.bridge_cap_w(c)
    for side in ("L", "R"):
        d = c.side[side]
        raw = d["raw"]
        d["kind"][mask] = URBAN
        raw["h"][mask] = S.BRIDGE_KERB_H
        raw["w"][mask] = cap_w
        d["mat"][mask] = 2
        raw["depth"][mask] = S.BRIDGE_DECK_THICKNESS + S.BRIDGE_KERB_H
        d["h"], d["w"], d["depth"] = smooth_1d(raw["h"], sig), smooth_1d(raw["w"], sig), smooth_1d(raw["depth"], sig)


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
        am = "apron_sett"
        if mat == MAT_FLUSH_ROAD:           # authored asphalt apron (ADR 0123): flush, same topology
            ha, am = 0.0, "road_asphalt"
            top = 0.02 * ap
        return [(0.0, 0.0, 0.0, ha, "curb_concrete"),
                (0.0, ha, ap, top, am),
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
        d = h if 0.05 < h < 1.5 else S.DITCH_DEPTH       # ditch depth per station (swale next to a path)
        u0 = ps + sw
        u2 = u0 + d * S.DITCH_SLOPE
        u3 = u2 + S.DITCH_BOTTOM_W
        u4 = u3 + (d - z1) * S.DITCH_SLOPE      # back slope rises d - z1 (z1 < 0): 1:1.5, was (d + z1) = 1:1.2
        return [(0.0, 0.0, ps, zp, "road_asphalt"),
                (ps, zp, u0, z1, "shoulder_gravel"),
                (u0, z1, u2, z1 - d, "verge_grass"),
                (u2, z1 - d, u3, z1 - d, "verge_grass"),
                (u3, z1 - d, u4, 0.0, "verge_grass"),
                (u4, 0.0, u4, -depth, "verge_grass")]
    tw = S.KERB_TOP_W
    zw = h + S.SIDEWALK_CROSSFALL * w
    if mat == MAT_FLUSH_ROAD:
        # flush edge (another carriageway touches / overlaps, a yard): the surface runs on, there is no kerb.
        # A concrete strip at road level used to cross the neighbour's lane edge (ADR 0076).
        # For a flush edge `h` is not a kerb height but the rise of the strip's outer edge (0 on ribbon edges; the
        # height of the neighbouring carriageway edge at junction corners, meshing._corner_gaps).
        z1 = h * tw / (tw + w)
        return [(0.0, 0.0, 0.0, 0.0, "road_asphalt"),
                (0.0, 0.0, tw, z1, "road_asphalt"),
                (tw, z1, tw + w, h, "road_asphalt"),
                (tw + w, h, tw + w, h - depth, "curb_concrete")]
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
