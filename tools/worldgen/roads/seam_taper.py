"""ADR 0275: width transitions across tile seams and at the end of a shoulder override.

Tiles are built one at a time from their own graph + overrides, so a road whose authored cross-section differs between
two tiles (an override that stops at the seam) met its other half with a step in the carriageway / asphalt edge. Here
every tile reads the *data in git* of its neighbours (region.yaml, roads.graph.json, overrides.yaml - never their
geometry or `generated/`), builds the neighbour's network with the same code and takes the cross-section the neighbour
would build at the seam BEFORE any seam transition ("nominal"). Both tiles then lay the two halves of one S-curve:

    value(x) = A + (B - A) * smoothstep(0.5 + x / L),   x = signed distance from the seam (A side: x < 0)

so on the seam both give the mean of the two nominal values (computed with a symmetric expression; shoulder widths in
whole centimetres) and the slope is continuous. L = RATIO x the largest step of an edge (carriageway edge, asphalt edge,
outer edge of the ground shoulder), clamped to MIN_LEN_M ... MAX_LEN_M and to twice the shorter of the two chains.

What is blended:
  * the carriageway half-width `Chain.hw` (apply_widths, right after the fork passes of pipeline.build_network);
    lanes of the touched sections share the local width (`lane_follow`, ADR 0233), otherwise the centre line would
    leave the axis inside the transition;
  * matching measured one-way cross-sections (ADR 0095): each edge gets the lesser D94 growth of the two ends;
    a more generous tile eases down to that width and axis at the cut, and the lane and paint positions follow;
  * the spacing of two P-7b lines where at least one has an authored spacing below GP class (ADR 0220);
  * the axis position (seams-w10): the lateral placement of D94 (network.gameplay_widen, shift towards the greater
    clearance) is decided per tile on that tile's piece of the edge, so the two halves of one road could meet with an
    axis step of lanes x GAMEPLAY_LANE_WIDEN_M / 2; both tiles move their axis half of the offset along the same
    S-curve (apply_widths). Ends are matched by the graph cut (`End.boundary_xy`), not by the shifted axis;
  * the paved and ground widths of the shoulder of a kerbless edge (ADR 0272, roads.xsec), carried per station in
    the side `mat` code (apply_shoulders, after every network.assign_sides). The same function turns a step of the
    shoulder widths between two sections of one chain (an override that ends inside the tile) into an S-curve
    centred on the step.

Length of the transition: PTB2022 (Dz.U. 2022 poz. 1518) § 17 ust. 6 only asks for a change of lane width "na krzywej
przejściowej lub prostej przejściowej w sposób płynny, bez widocznych załamań krawędzi" - no number, and nothing on
shoulders. RATIO / MIN_LEN_M / MAX_LEN_M are ESTIMATED.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from . import network as Nw

from . import xsec as X               # ADR 0272: shoulder of a kerbless edge as data

REPO = Path(__file__).resolve().parents[3]
REGIONS = REPO / "Data" / "Regions"

RATIO = 100.0          # ESTIMATED: transition length per metre of edge step (edge skew 1:100 on average, 1:67 at most)
MIN_LEN_M = 20.0       # ESTIMATED
MAX_LEN_M = 80.0       # ESTIMATED
MIN_STEP_M = 0.005     # steps below this are left alone (float noise of two builds of the same data)
SEAM_EPS_M = 0.05      # a chain end lies on the seam line within this distance
MATCH_M = 0.5          # the two halves of a road cut at the seam: same OSM way, ends within this distance
MIN_RAMP_HALF_M = 0.5  # an in-chain shoulder step with less room than this on a side stays a step


def _smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def weight(d, length):
    """Share of the way from the tile's own value to the seam value at distance d from the seam: 1 on the seam,
    0 from length / 2 on (half of one smoothstep laid across the seam)."""
    return 2.0 * _smoothstep(0.5 - np.asarray(d, float) / float(length))


# --------------------------------------------------------------------------------------------- seam geometry
def shared_edge(ba, bb):
    """Shared edge of two axis-aligned bboxes (xmin, ymin, xmax, ymax): dict(axis 'x'|'y', at, lo, hi, normal_ab)
    or None (corner / no contact). normal_ab: unit vector pointing from a into b."""
    ax0, ay0, ax1, ay1 = ba
    bx0, by0, bx1, by1 = bb
    for at, nab in ((ax1, (1.0, 0.0)) if abs(ax1 - bx0) < 1e-6 else (None, None),
                    (ax0, (-1.0, 0.0)) if abs(ax0 - bx1) < 1e-6 else (None, None)):
        if at is not None:
            lo, hi = max(ay0, by0), min(ay1, by1)
            if hi - lo > 1.0:
                return {"axis": "x", "at": at, "lo": lo, "hi": hi, "normal_ab": nab}
    for at, nab in ((ay1, (0.0, 1.0)) if abs(ay1 - by0) < 1e-6 else (None, None),
                    (ay0, (0.0, -1.0)) if abs(ay0 - by1) < 1e-6 else (None, None)):
        if at is not None:
            lo, hi = max(ax0, bx0), min(ax1, bx1)
            if hi - lo > 1.0:
                return {"axis": "y", "at": at, "lo": lo, "hi": hi, "normal_ab": nab}
    return None


def on_seam(xy, se) -> bool:
    k = 0 if se["axis"] == "x" else 1
    return abs(xy[k] - se["at"]) <= SEAM_EPS_M and se["lo"] - SEAM_EPS_M <= xy[1 - k] <= se["hi"] + SEAM_EPS_M


def _bbox(region: dict):
    b = region["bbox"]
    return (float(b["xmin"]), float(b["ymin"]), float(b["xmax"]), float(b["ymax"]))


# --------------------------------------------------------------------------------------------- chain ends
@dataclass(frozen=True)
class MeasuredLanes:
    base: tuple                  # width and lane edges before D94
    growth: tuple                # increase of the travel-left and travel-right edges
    dirn: int                    # direction of travel relative to the chain
    length: float                # distance from the cut to the next section (or the end of the chain)


@dataclass(frozen=True)
class End:
    """Nominal cross-section of a chain end on the tile boundary (before any seam transition)."""
    chain: str
    end: int                  # 0 | -1
    osm_way: int
    xy: tuple                 # EPSG:2180
    left: tuple               # unit normal of the chain's left side at the end (world frame)
    hw: float                 # carriageway half-width
    length: float             # chain length
    shoulder: dict            # {"L" / "R": (paved_cm, ground_cm) | None}: ADR 0272 rule / override of the end section
    blendable: bool = True    # False: the lanes of the end section cannot follow a changing width (ADR 0095 data)
    boundary_xy: tuple | None = None  # graph boundary before lateral placement (D94)
    edge_line_spacing: float | None = None
    authored_spacing: bool = False
    measured_lanes: MeasuredLanes | None = None

    def on_seam(self, se) -> bool:
        """Tile membership uses the graph cut, even if lateral placement moved the axis off its plane."""
        return on_seam(self.boundary_xy if self.boundary_xy is not None else self.xy, se)


def _osm_way(edge_id: str) -> int:
    return int(edge_id.split(":")[0].lstrip("w"))


def nominal_shoulder(sec, rev: bool) -> dict:
    """{"L" / "R": (paved_cm, ground_cm) | None} of a section in the chain frame (roads.xsec.resolve: override >
    OSM shoulder=* > class rule); None = a kerb forced by an override, or a roundabout."""
    out = {"L": None, "R": None}
    if getattr(sec, "roundabout", False):
        return out
    for side, osm in (("L", "left"), ("R", "right")):
        if rev:
            osm = "right" if osm == "left" else "left"
        sh = X.resolve(sec, osm)
        if sh.force != "kerb":
            out[side] = (int(round(sh.paved_m * 100)), int(round(sh.ground_m * 100)))
    return out


def ends(net: Nw.Network) -> list[End]:
    """Chain ends on the tile boundary (graph node flag `boundary`, degree 1), in a stable order."""
    from . import markings as MK

    o = np.asarray(net.origin, float)
    out = []
    for c in net.chains:
        if c.closed or c.roundabout or c.meta.get("absorbed") or len(c.line.s) < 2:
            continue
        for e, node in ((0, c.node_a), (-1, c.node_b)):
            nd = net.nodes.get(node) or {}
            if not nd.get("boundary") or nd.get("deg") != 1:
                continue
            sec = net.sec_list[int(c.sec_idx[e])]
            rev = bool(c.meta["rev"][e]) if "rev" in c.meta else False
            pg = c.line.p[e] + o
            n = c.line.n[e]
            spacing = None
            if sec.cls not in ("A", "S", "GP") and not sec.lane_edges and sec.highway in MK.MARKED:
                lines = MK.edge_lines(sec, float(c.hw[e]), c.dirn[e])
                if len(lines) == 2:
                    spacing = abs(float(lines[1][0] - lines[0][0]))
            measured = None
            if sec.lane_edges and sec.oneway and abs(2 * c.hw[e] - sec.width) < 0.001:
                add = sec.provenance.get("gameplay_widen_m", 0.0)
                shift = sec.provenance.get("gameplay_shift_left_m", 0.0)
                base = sec.gameplay_lane_base or (sec.width, *sec.lane_edges)
                order = slice(None, None, 1 if e == 0 else -1)
                next_sec = np.flatnonzero(c.sec_idx[order] != c.sec_idx[e])
                stop = int(next_sec[0]) if len(next_sec) else len(c.line.s) - 1
                length = abs(float(c.line.s[order][stop] - c.line.s[e]))
                growth = (round(add / 2 + shift, 4), round(add / 2 - shift, 4))
                measured = MeasuredLanes(base, growth, int(c.dirn[e]), length)
            out.append(End(chain=c.id, end=e, osm_way=_osm_way(sec.edge_id), xy=(float(pg[0]), float(pg[1])),
                           left=(float(n[0]), float(n[1])), hw=float(c.hw[e]), length=float(c.line.s[-1]),
                           shoulder=nominal_shoulder(sec, rev),
                           blendable=not (sec.lane_edges or (sec.width_profile and not sec.lane_follow)),
                           boundary_xy=tuple(np.asarray(nd["xy"]) + o), edge_line_spacing=spacing,
                           authored_spacing=sec.edge_line_spacing is not None, measured_lanes=measured))
    return out


# --------------------------------------------------------------------------------------------- plan
@dataclass
class Taper:
    chain: str
    end: int
    length: float                     # full length L of the S-curve; this tile lays L / 2 from the seam
    hw_own: float
    hw_other: float
    hw_seam: float
    shoulder: dict = field(default_factory=dict)   # own side "L"/"R" -> {"own": (p, g), "other": (p, g), "seam": (p, g)} cm
    neighbour: str | None = None
    other_chain: str | None = None
    step_m: float = 0.0               # the largest edge step that set the length
    skipped: str | None = None        # reason the carriageway width is not blended
    shift_seam: tuple = (0.0, 0.0)    # seams-w10: move of the axis end on the seam (world frame, m) = half of the vector
    #                                   between the two nominal axis ends: both tiles meet in the middle
    axis_offset: float = 0.0          # seams-w10: distance of the two nominal axis ends (the same in both tiles)
    edge_line_spacing: float | None = None
    d94: bool = False

    def report(self) -> dict:
        r = {"chain": self.chain, "end": "a" if self.end == 0 else "b", "neighbour": self.neighbour,
             "length_m": round(self.length, 2), "in_tile_m": round(self.length / 2, 2), "step_m": round(self.step_m, 3),
             "width_own": round(2 * self.hw_own, 3), "width_other": round(2 * self.hw_other, 3),
             "width_seam": round(2 * self.hw_seam, 3)}
        if self.axis_offset:
            r["axis_offset_m"] = round(self.axis_offset, 3)
        if self.edge_line_spacing is not None:
            r["edge_line_spacing_seam_m"] = round(self.edge_line_spacing, 3)
        if self.d94:
            r["d94_shared_clearance"] = True
        if self.shoulder:
            r["shoulder_cm"] = {k: {a: list(b) for a, b in v.items()} for k, v in sorted(self.shoulder.items())}
        if self.skipped:
            r["skipped"] = self.skipped
        return r


def _mean_cm(a: int, b: int) -> int:
    return (a + b + 1) // 2           # symmetric in (a, b): both tiles get the same centimetre


def _cut(e: End) -> tuple:
    """The graph cut of the end (identical in both tiles: the same OSM way clipped by the same bbox edge); the built
    axis may sit off it by the lateral placement (D94 / ADR 0077), differently in each tile."""
    return e.boundary_xy if e.boundary_xy is not None else e.xy


def match(own: list[End], other: list[End]) -> list[tuple[End, End]]:
    """Mutually nearest ends of the same OSM way within MATCH_M (the same pairs whichever tile asks). Distance between
    the graph cuts (seams-w10): two halves whose D94 shifts go opposite ways (0.25 + 0.25 m) are still one road."""
    def near(e, cands):
        best = None
        for x in cands:
            if x.osm_way != e.osm_way:
                continue
            d = math.hypot(_cut(e)[0] - _cut(x)[0], _cut(e)[1] - _cut(x)[1])
            if d <= MATCH_M and (best is None or (d, x.xy) < best[:2]):
                best = (d, x.xy, x)
        return best[2] if best else None
    out = []
    for e in own:
        x = near(e, other)
        if x is not None and near(x, own) is e:
            out.append((e, x))
    return out


def _d94_target(e: End, x: End, same: bool):
    """Common growth of matching measured lanes. Neither tile spends clearance unavailable on the other side."""
    a, b = e.measured_lanes, x.measured_lanes
    if a is None or b is None or a.base != b.base or a.growth == b.growth or (a.dirn == b.dirn) != same:
        return None
    growth = tuple(min(va, vb) for va, vb in zip(a.growth, b.growth))
    hw = (a.base[0] + sum(growth)) / 2
    if growth == a.growth:
        xy = e.xy
    elif growth == b.growth:
        xy = x.xy
    else:
        # On opposing allocations both tiles give up growth on one side. Reconstruct the
        # base axes, then add the same permitted imbalance in the travel frame.
        shift_a = ((growth[0] - growth[1]) - (a.growth[0] - a.growth[1])) / 2
        shift_b = ((growth[0] - growth[1]) - (b.growth[0] - b.growth[1])) / 2
        xy = tuple((pa + na * a.dirn * shift_a + pb + nb * b.dirn * shift_b) / 2
                   for pa, pb, na, nb in zip(e.xy, x.xy, e.left, x.left))
    return hw, xy, min(a.length, b.length)


def plan_pair(e: End, x: End, neighbour: str | None = None) -> Taper | None:
    """Transition of own end `e` towards the nominal section `x` of the neighbour; None when they already agree."""
    same = (e.left[0] * x.left[0] + e.left[1] * x.left[1]) > 0      # the neighbour's chain runs the same way
    dhw = x.hw - e.hw
    steps = [abs(dhw)] if (e.blendable and x.blendable) else []
    spacing = None
    if (e.authored_spacing or x.authored_spacing) and e.edge_line_spacing is not None and x.edge_line_spacing is not None:
        from .markings import EDGE_LINE_MIN_INSET

        spacing_step = abs(e.edge_line_spacing - x.edge_line_spacing) / 2
        if spacing_step >= MIN_STEP_M or abs(dhw) >= MIN_STEP_M:
            capacity = e.hw + x.hw if e.blendable and x.blendable else 2 * min(e.hw, x.hw)
            spacing = min((e.edge_line_spacing + x.edge_line_spacing) / 2, capacity - 2 * EDGE_LINE_MIN_INSET)
            steps.append(spacing_step)
    sh = {}
    for side in ("L", "R"):
        a, b = e.shoulder.get(side), x.shoulder.get(side if same else ("R" if side == "L" else "L"))
        if a is None or b is None or a == b:
            continue
        sh[side] = {"own": a, "other": b, "seam": (_mean_cm(a[0], b[0]), _mean_cm(a[1], b[1]))}
        steps.append(abs(b[0] - a[0]) / 100.0)                                   # asphalt edge beside the carriageway
        steps.append(abs((b[0] + b[1]) - (a[0] + a[1])) / 100.0)                 # outer edge of the ground part
    blend_hw = e.blendable and x.blendable
    step = max(steps, default=0.0)
    if blend_hw and sh:
        # asphalt edge = half-width + paved part: the two steps add up (or cancel)
        step = max([step] + [abs(dhw + (v["other"][0] - v["own"][0]) / 100.0) for v in sh.values()])
    skipped = None
    if not blend_hw and abs(dhw) >= MIN_STEP_M:
        skipped = "lane_edges / width profile without lanes_follow_width on the end section (ADR 0095)"
    # seams-w10: lateral offset of the two nominal axes on the seam. D94 (network.gameplay_widen) shifts a carriageway
    # towards its greater clearance, measured on this tile's piece of the edge only, so the two halves of one road can
    # be shifted differently (0.125 / 0.25 / 0.375 m = lanes x GAMEPLAY_LANE_WIDEN_M / 2). Triggered by the offset
    # across the common normal (the same bits in both tiles: a + b == b + a, a negated vector is exact); the end then
    # moves by half of the whole vector, so both ends land on one point even where the two smoothed axes leave the
    # seam at slightly different angles (a shift along each tile's own normal would leave a few centimetres).
    xl = (x.left[0], x.left[1]) if same else (-x.left[0], -x.left[1])
    nx, ny = e.left[0] + xl[0], e.left[1] + xl[1]
    nn = math.hypot(nx, ny) or 1.0
    vx, vy = x.xy[0] - e.xy[0], x.xy[1] - e.xy[1]
    dlat = (vx * nx + vy * ny) / nn
    shift, offset = (0.0, 0.0), 0.0
    if abs(dlat) >= MIN_STEP_M:
        offset = math.hypot(vx, vy)
        shift = (0.5 * vx, 0.5 * vy)
        step += offset               # both carriageway edges move with the axis: upper bound of the edge step
    d94 = _d94_target(e, x, same)
    hw_seam = 0.5 * (e.hw + x.hw) if blend_hw else e.hw
    limit = min(e.length, x.length)
    if d94 is not None:
        hw_seam, xy, limit = d94
        shift = tuple(p - q for p, q in zip(xy, e.xy))
        offset = math.hypot(vx, vy)
        step = max(step, e.hw - hw_seam, x.hw - hw_seam, offset)
        skipped = None
    if step < MIN_STEP_M and not skipped:
        return None
    length = min(max(RATIO * step, MIN_LEN_M), MAX_LEN_M, 2.0 * limit)
    return Taper(chain=e.chain, end=e.end, length=float(length), hw_own=e.hw, hw_other=x.hw,
                 hw_seam=hw_seam, shoulder=sh, neighbour=neighbour,
                 other_chain=x.chain, step_m=float(step), skipped=skipped, shift_seam=shift, axis_offset=float(offset),
                 edge_line_spacing=spacing, d94=d94 is not None)


def plan(own: list[End], others: dict) -> list[Taper]:
    """others: {neighbour id: [End, ...]} (ends of the neighbour on the shared edge)."""
    out = []
    for nb in sorted(others):
        for e, x in match(own, others[nb]):
            t = plan_pair(e, x, nb)
            if t is not None:
                out.append(t)
    out.sort(key=lambda t: (t.chain, t.end))
    return out


# --------------------------------------------------------------------------------------------- neighbours (data in git)
def plain_network(graph: dict, origin, overrides: list) -> Nw.Network:
    """The network of pipeline.build_network WITHOUT seam transitions: what a tile builds on its own."""
    net = Nw.load(graph, origin, overrides)
    Nw.taper_forks(net, [])
    Nw.align_forks(net, [])
    Nw.abreast_forks(net, [])
    return net


def neighbours(region_id: str, regions: Path | None = None) -> list[tuple[str, dict]]:
    """[(neighbour id, shared edge)] of the tiles in Data/Regions that share an edge with this one."""
    regions = regions or REGIONS
    own = yaml.safe_load((regions / region_id / "region.yaml").read_text(encoding="utf-8"))
    out = []
    for d in sorted(p for p in regions.iterdir() if p.is_dir() and p.name != region_id):
        if not ((d / "region.yaml").exists() and (d / "roads.graph.json").exists()):
            continue
        reg = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
        if not reg or "bbox" not in reg:
            continue
        se = shared_edge(_bbox(own), _bbox(reg))
        if se:
            out.append((d.name, se))
    return out


def _load_overrides(d: Path) -> list:
    """The neighbour's overrides as its own build sees them: the tool-written files of pipeline.GENERATED_OVERRIDES
    (ADR 0301: overrides.ortho_lanes.json lays out seam edges) first, then overrides.yaml."""
    import json
    from .pipeline import GENERATED_OVERRIDES
    out = []
    for name in GENERATED_OVERRIDES:
        g = d / name
        if g.exists():
            out += json.loads(g.read_text(encoding="utf-8")).get("overrides", []) or []
    p = d / "overrides.yaml"
    if not p.exists():
        return out
    return out + ((yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("overrides", []) or [])


def neighbour_ends(region_id: str, own: list[End], regions: Path | None = None) -> dict:
    """{neighbour id: [End, ...]} on the shared edges. A neighbour is loaded only when this tile has a chain end on
    the shared edge."""
    regions = regions or REGIONS
    out = {}
    for nb, se in neighbours(region_id, regions):
        if not any(e.on_seam(se) for e in own):
            continue
        d = regions / nb
        reg = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
        graph = json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))
        net = plain_network(graph, (reg["origin"]["x"], reg["origin"]["y"]), _load_overrides(d))
        out[nb] = [e for e in ends(net) if e.on_seam(se)]
    return out


def plan_region(net: Nw.Network, region_id: str, regions: Path | None = None) -> list[Taper]:
    """Transitions of a tile against the neighbours' data. Call on the network BEFORE apply_widths."""
    own = ends(net)
    if not own:
        return []
    return plan(own, neighbour_ends(region_id, own, regions))


# --------------------------------------------------------------------------------------------- apply
def _chains(net):
    return {c.id: c for c in net.chains}


def apply_widths(net: Nw.Network, tapers: list[Taper]) -> list[dict]:
    """Blend the carriageway half-width and the axis position (seams-w10) of the planned chain ends; returns the report
    rows."""
    from . import markings as MK

    by = _chains(net)
    for t in tapers:
        c = by[t.chain]
        d = c.line.s if t.end == 0 else c.line.s[-1] - c.line.s
        # The capped D94 width has a flat derivative at the cut, where the constrained tile
        # may already have its final width throughout the section.
        k = _smoothstep(1.0 - 2.0 * d / t.length) if t.d94 else weight(d, t.length)
        if any(t.shift_seam):
            # seams-w10: the axis follows the same S-curve to the middle of the two nominal axis ends (lateral
            # placement like ADR 0077: its share across the axis goes to meta center_offset, so fidelity does not read
            # it as a deviation from the OSM way)
            mv = k[:, None] * np.asarray(t.shift_seam, float)[None, :]
            lat = (mv * c.line.n).sum(axis=1)
            c.line = Nw.Polyline(c.line.p + mv)
            prev = c.meta.get("center_offset")
            c.meta["center_offset"] = lat if prev is None or len(prev) != len(lat) else prev + lat
        dhw = t.hw_seam - t.hw_own
        if t.skipped or abs(dhw) < MIN_STEP_M / 2:
            continue
        c.hw = c.hw + dhw * k
        for i in np.unique(c.sec_idx[k > 0]):
            sec = net.sec_list[int(i)]
            if t.d94:
                sec.lane_edges_follow_width = True
            elif not sec.lane_follow and not sec.lane_edges:
                sec.lane_follow = True                    # lanes share the local width inside the transition
                sec.provenance["lanes_follow_width"] = "derived:seam_taper (ADR 0275)"
        m = max(2, int(math.ceil(2 * float(c.hw.max()) / 1.75)))
        c.m_lat = m + (m % 2)
    for t in tapers:
        if t.edge_line_spacing is None:
            continue
        c = by[t.chain]
        sec = net.sec_list[int(c.sec_idx[t.end])]
        lines = MK.edge_lines(sec, float(c.hw[t.end]), c.dirn[t.end])
        own = abs(float(lines[1][0] - lines[0][0]))
        d = np.abs(c.line.s - c.line.s[t.end])
        delta = c.meta.setdefault("edge_line_spacing_delta", np.zeros_like(c.hw))
        delta += (t.edge_line_spacing - own) * weight(d, t.length)
    return [t.report() for t in tapers]


def _decode(mat: np.ndarray):
    code = X.SHOULDER_CODE
    v = np.where(mat >= code, mat - code, 0)
    lp, lg = int(round(X.LEGACY[0] * 100)), int(round(X.LEGACY[1] * 100))
    return (np.where(mat >= code, v // 1000, lp).astype(float), np.where(mat >= code, v % 1000, lg).astype(float))


def _encode(paved_cm: np.ndarray, ground_cm: np.ndarray) -> np.ndarray:
    p, g = np.rint(paved_cm).astype(np.int64), np.rint(ground_cm).astype(np.int64)
    lp, lg = int(round(X.LEGACY[0] * 100)), int(round(X.LEGACY[1] * 100))
    return np.where((p == lp) & (g == lg), 0, X.SHOULDER_CODE + p * 1000 + g)


def _ramp_steps(s: np.ndarray, pv: np.ndarray, gr: np.ndarray) -> int:
    """One run of kerbless stations: every step of (paved, ground) between neighbours becomes an S-curve centred on
    the step. In place; returns the number of ramps."""
    cut = np.where((np.diff(pv) != 0) | (np.diff(gr) != 0))[0]
    if not len(cut):
        return 0
    p0, g0 = pv.copy(), gr.copy()
    pos = [0.5 * (s[j] + s[j + 1]) for j in cut]
    bounds = [s[0]] + pos + [s[-1]]
    n = 0
    for q, j in enumerate(cut):
        a, b = (p0[j], g0[j]), (p0[j + 1], g0[j + 1])
        step = max(abs(b[0] - a[0]), abs((b[0] + b[1]) - (a[0] + a[1]))) / 100.0
        room_l = (bounds[q + 1] - bounds[q]) * (1.0 if q == 0 else 0.5)
        room_r = (bounds[q + 2] - bounds[q + 1]) * (1.0 if q == len(cut) - 1 else 0.5)
        h = min(0.5 * min(max(RATIO * step, MIN_LEN_M), MAX_LEN_M), room_l, room_r)
        if h < MIN_RAMP_HALF_M:
            continue
        m = np.abs(s - pos[q]) <= h
        f = _smoothstep((s[m] - (pos[q] - h)) / (2.0 * h))
        pv[m] = a[0] + (b[0] - a[0]) * f
        gr[m] = a[1] + (b[1] - a[1]) * f
        n += 1
    return n


def apply_shoulders(net: Nw.Network, tapers: list[Taper] | None = None) -> dict:
    """After network.assign_sides: S-curves of the shoulder widths (side `mat` codes of kerbless stations) at steps
    inside a chain and towards the seam value of the planned ends."""
    rep = {"in_chain_ramps": 0, "seam_sides": 0}
    seam = {}
    for t in tapers or []:
        for side, v in t.shoulder.items():
            seam[(t.chain, side)] = seam.get((t.chain, side), []) + [(t, v)]
    for c in net.chains:
        if c.roundabout or not c.side:
            continue
        for side in ("L", "R"):
            d = c.side.get(side)
            if not d:
                continue
            mat = np.asarray(d["mat"]).astype(np.int64)
            rural = (np.asarray(d["kind"]) == Nw.RURAL) & ((mat == 0) | (mat >= X.SHOULDER_CODE))
            if not rural.any():
                continue
            pv, gr = _decode(mat)
            idx = np.arange(len(mat))
            for run in np.split(idx, np.where(np.diff(rural.astype(int)) != 0)[0] + 1):
                if len(run) >= 2 and rural[run[0]]:
                    p, g = pv[run], gr[run]
                    rep["in_chain_ramps"] += _ramp_steps(c.line.s[run], p, g)
                    pv[run], gr[run] = p, g
            for t, v in seam.get((c.id, side), []):
                dist = c.line.s if t.end == 0 else c.line.s[-1] - c.line.s
                k = weight(dist, t.length)
                pv = v["seam"][0] + (pv - v["seam"][0]) * (1.0 - k)
                gr = v["seam"][1] + (gr - v["seam"][1]) * (1.0 - k)
                rep["seam_sides"] += 1
            new = np.where(rural, _encode(pv, gr), mat)
            if (new != mat).any():
                d["mat"] = new
    return rep


def shoulder_at(c, side: str, i: int):
    """(paved_m, ground_m) of a kerbless station, None beside a kerb."""
    d = (c.side or {}).get(side)
    if not d or int(d["kind"][i]) != Nw.RURAL:
        return None
    p, g = _decode(np.asarray([int(d["mat"][i])], dtype=np.int64))
    return float(p[0]) / 100.0, float(g[0]) / 100.0


# --------------------------------------------------------------------------------------------- side kind (seams-side-s24)
# The side profile at a seam end (kerb / kerb + sidewalk / flat edge / kerbless rural shoulder) is decided per tile by
# network.assign_sides from data clipped to the tile bbox: footways of osm_context, BDOT10k OT_SKRP_L paths and the
# OT_PTPL_A / parking yards stop at the bbox, the majority windows (+-20 m walk, +-12 m yard) run out at the seam and
# the junction trims of the second pass (ADR 0304) only see the tile's own junctions. The two halves of one road then
# met with a kerb against a flat edge, a sidewalk on one side only, or a kerb against a rural shoulder (qa.seams FAIL
# "pobocze L/P", artifacts/seams-w10-s24). Like the widths above, both tiles now compute the NOMINAL side profile of
# both seam ends with the same code from the same data in git (graph, overrides, generated/osm_context.json,
# generated/streetscape_sources.json; plain network + junctions + the second assign_sides pass on the seam chains),
# agree on one value per side with a symmetric rule and impose it on their own end:
#
#   the median profile takes precedence over an open rural shoulder if the opposing carriageway is visible on one tile;
#   otherwise: constrained (another carriageway at the edge: tight kerb / flush strip, never changed) > kerb + sidewalk >
#         flat edge (yard, h = 0) > kerb > kerbless rural shoulder; equal kinds: the wider sidewalk.
#
# Clipping only ever REMOVES evidence (a footway or a yard that one tile still sees near the seam is real data), and a
# narrower edge profile never reaches onto anything, so the higher rank wins. The imposed value covers the run of the
# end's own kind from the seam inwards, at most SIDE_HOLD_M (WORKING_VALUE); the step of kinds then lies inside one
# tile, where the mesh already joins profile changes along a chain.
SIDE_HOLD_M = 25.0      # WORKING_VALUE: longest run of the end's kind replaced by the agreed seam profile
CAT_RANK = {"rural": 1, "kerb": 2, "flat": 3, "sidewalk": 4, "constrained": 5}


@dataclass(frozen=True)
class SideVal:
    """Side profile of one station, frame-free (kind / h / w / mat / walk / verge / depth as network.assign_sides)."""
    cat: str                  # constrained | sidewalk | flat | kerb | rural | median | other
    kind: int
    h: float
    w: float
    depth: float
    mat: int
    walk: bool
    verge: float


def side_cat(d: dict, i: int) -> str:
    kind = int(d["kind"][i])
    if kind == Nw.MEDIAN_RURAL:
        return "median"
    if kind not in (Nw.URBAN, Nw.RURAL):
        return "other"
    tight = d.get("tight")
    if int(d["mat"][i]) == Nw.MAT_FLUSH_ROAD or (tight is not None and bool(tight[i])):
        return "constrained"
    if kind == Nw.RURAL:
        return "rural"
    if bool(d["walk"][i]) and float(d["raw"]["w"][i]) > 0.05:
        return "sidewalk"
    return "flat" if float(d["raw"]["h"][i]) < 0.05 else "kerb"


def side_val(c, side: str, i: int) -> SideVal | None:
    d = (c.side or {}).get(side)
    if not d:
        return None
    vg = d.get("verge")
    return SideVal(cat=side_cat(d, i), kind=int(d["kind"][i]), h=float(d["raw"]["h"][i]), w=float(d["raw"]["w"][i]),
                   depth=float(d["raw"]["depth"][i]), mat=int(d["mat"][i]), walk=bool(d["walk"][i]),
                   verge=float(vg[i]) if vg is not None else 0.0)


def side_inputs(ctx: dict | None, ss: dict | None, overrides: list, origin):
    """(footways, walkways, yards) of network.assign_sides from osm_context + streetscape_sources: the inputs of
    pipeline.build (one definition for the generator, the nominal seam sides and qa.seams)."""
    import shapely
    from shapely.geometry import LineString, Polygon
    o = np.asarray(origin, float)
    fw = [f for f in (ctx or {}).get("footways", []) if len(f["geometry"]) >= 2]
    foot = [LineString(np.array(f["geometry"]) - o) for f in fw]
    walk = [LineString(np.array(f["geometry"]) - o) for f in fw if f["highway"] != "path"]
    yards = None
    if ss is not None:
        walk += [LineString(np.array(f["geometry"]["coordinates"]) - o) for f in ss["bdot10k"]["OT_SKRP_L"]
                 if f["props"].get("materialnawierzchni") not in (None, "grunt naturalny")]
        polys = [Polygon(np.array(f["geometry"]["coordinates"][0]) - o) for f in ss["bdot10k"]["OT_PTPL_A"]
                 if f["props"].get("materialnawierzchni") != "grunt naturalny"]
        polys += [Polygon(np.array(a["geometry"]["coordinates"][0]) - o) for a in ss["osm"]["areas"]
                  if a["tags"].get("amenity") == "parking"]
        polys += [Polygon(np.asarray(ov["polygon_epsg2180"], float) - o,
                          [np.asarray(h, float) - o for h in ov.get("holes_epsg2180", [])])
                  for ov in overrides if ov.get("kind") == "paved_area"]
        yards = shapely.union_all([shapely.make_valid(p) for p in polys])
        shapely.prepare(yards)
    return foot, walk, yards


def nominal_sides(graph: dict, origin, overrides: list, ctx: dict | None, ss: dict | None,
                  region_id: str | None = None) -> tuple[list[End], dict]:
    """([End], {(chain, end): {"L" / "R": SideVal | None}}) of a tile on its own: plain network (no seam transitions),
    its junctions (trims) and the second assign_sides pass on the chains with a boundary end - what the tile's build
    meshes at the seam before the agreement. The same call in every tile that asks (data in git only)."""
    from . import junctions as J
    net = plain_network(graph, origin, overrides)
    own = ends(net)
    if not own:
        return [], {}
    net.region_id, net.authored = region_id, overrides          # implied sidewalks (ADR 0237 D38) as pipeline.build
    o = np.asarray(origin, float)
    J.build_junctions(net, [dict(p, e=p["x"] - o[0], n=p["y"] - o[1]) for p in (ctx or {}).get("points", [])])
    foot, walk, yards = side_inputs(ctx, ss, overrides, origin)
    Nw.assign_sides(net, foot, built_up=True, walkways=walk, yards=yards, trims=True, only={e.chain for e in own})
    by = _chains(net)
    out = {}
    for e in own:
        c = by[e.chain]
        i = 0 if e.end == 0 else len(c.line.s) - 1
        out[(e.chain, e.end)] = {s: side_val(c, s, i) for s in ("L", "R")}
    return own, out


def _region_files(d: Path):
    def rj(p):
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    reg = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
    return ((reg["origin"]["x"], reg["origin"]["y"]), rj(d / "roads.graph.json"), _load_overrides(d),
            rj(d / "generated" / "osm_context.json"), rj(d / "generated" / "streetscape_sources.json"))


def region_nominal_sides(region_id: str, regions: Path | None = None) -> tuple[list[End], dict]:
    d = (regions or REGIONS) / region_id
    origin, graph, ov, ctx, ss = _region_files(d)
    return nominal_sides(graph, origin, ov, ctx, ss, region_id)


@dataclass
class SideFix:
    chain: str
    end: int
    side: str                 # own chain side "L" / "R"
    want: SideVal             # the agreed seam profile
    own: SideVal              # own nominal
    other: SideVal            # neighbour's nominal (its side facing the same way)
    neighbour: str | None = None
    applied_m: float = 0.0
    kept: str | None = None   # why the own end was not changed

    def report(self) -> dict:
        r = {"chain": self.chain, "end": "a" if self.end == 0 else "b", "side": self.side, "neighbour": self.neighbour,
             "own": self.own.cat, "other": self.other.cat, "seam": self.want.cat, "applied_m": round(self.applied_m, 1)}
        if self.want.cat == "sidewalk":
            r["sidewalk_w"] = round(self.want.w, 2)
        if self.kept:
            r["kept"] = self.kept
        return r


def agree(a: SideVal | None, b: SideVal | None) -> SideVal | None:
    """The seam profile of two nominal ends (symmetric: agree(a, b) == agree(b, a)); None = leave both as they are."""
    if a is None or b is None or "other" in (a.cat, b.cat):
        return None
    if "median" in (a.cat, b.cat):
        # A tile that sees the opposing carriageway retains the narrower median profile
        # when its neighbour sees only an open shoulder in the clipped context.
        return (a if a.cat == "median" else b) if "rural" in (a.cat, b.cat) else None
    if a.cat == b.cat:
        if a.cat == "constrained":
            return None
        if a.cat == "sidewalk" and abs(a.w - b.w) > 1e-6:
            return a if a.w > b.w else b
        return a
    if "constrained" in (a.cat, b.cat):
        return a if a.cat == "constrained" else b
    return a if CAT_RANK[a.cat] > CAT_RANK[b.cat] else b


def plan_sides(own: list[End], own_sides: dict, others: dict) -> list[SideFix]:
    """others: {neighbour id: ([End], {(chain, end): sides})} -> the agreed profile of every matched seam end side."""
    out = []
    for nb in sorted(others):
        x_ends, x_sides = others[nb]
        for e, x in match(own, x_ends):
            same = (e.left[0] * x.left[0] + e.left[1] * x.left[1]) > 0
            sa, sb = own_sides.get((e.chain, e.end)) or {}, x_sides.get((x.chain, x.end)) or {}
            for side in ("L", "R"):
                a, b = sa.get(side), sb.get(side if same else ("R" if side == "L" else "L"))
                w = agree(a, b)
                if w is not None:
                    out.append(SideFix(chain=e.chain, end=e.end, side=side, want=w, own=a, other=b, neighbour=nb))
    out.sort(key=lambda f: (f.chain, f.end, f.side))
    return out


def plan_sides_region(region_id: str, own: tuple | None = None, regions: Path | None = None) -> list[SideFix]:
    """Agreed seam side profiles of a tile against the neighbours' data (all from git: no geometry, no derived)."""
    regions = regions or REGIONS
    own = own or region_nominal_sides(region_id, regions)
    if not own[0]:
        return []
    others = {}
    for nb, se in neighbours(region_id, regions):
        if any(e.on_seam(se) for e in own[0]):
            x_ends, x_sides = region_nominal_sides(nb, regions)
            others[nb] = ([e for e in x_ends if e.on_seam(se)], x_sides)
    return plan_sides(own[0], own[1], others)


def apply_sides(net: Nw.Network, fixes: list[SideFix]) -> list[dict]:
    """After the last network.assign_sides, before apply_shoulders: the own end takes the agreed seam profile over the
    run of its own kind (<= SIDE_HOLD_M). Constrained stations, other kinds (median, island) and bridges are kept."""
    by = _chains(net)
    for f in fixes:
        c = by.get(f.chain)
        d = (c.side or {}).get(f.side) if c is not None else None
        if d is None or c.meta.get("absorbed"):
            f.kept = "no chain / side in the built network"
            continue
        n = len(c.line.s)
        i0 = 0 if f.end == 0 else n - 1
        cur = side_cat(d, i0)
        if cur == f.want.cat and not (cur == "sidewalk" and abs(float(d["raw"]["w"][i0]) - f.want.w) > 1e-6):
            continue
        if cur in ("constrained", "other"):
            f.kept = f"own end is {cur}"
            continue
        dist = c.line.s if f.end == 0 else c.line.s[-1] - c.line.s
        sel = []
        for i in (range(n) if f.end == 0 else range(n - 1, -1, -1)):
            if dist[i] > SIDE_HOLD_M or side_cat(d, i) != cur or bool(c.bridge[i]):
                break
            sel.append(i)
        if not sel:
            f.kept = "seam station on a bridge"
            continue
        sel = np.asarray(sel)
        w = f.want
        mat = np.asarray(d["mat"]).astype(np.int64)
        if w.cat == "rural":                     # own shoulder code of the section (ADR 0272), tapered by apply_shoulders
            codes = []
            for i in sel:
                osm = {"L": "left", "R": "right"}[f.side]
                if bool(c.meta["rev"][i]):
                    osm = "right" if osm == "left" else "left"
                codes.append(X.resolve(net.sec_list[int(c.sec_idx[i])], osm).code)
            mat[sel] = np.asarray(codes, np.int64)
        else:
            mat[sel] = w.mat
        kind = np.asarray(d["kind"]).copy()
        kind[sel] = w.kind
        d["kind"], d["mat"] = kind, mat
        for k, v in (("h", w.h), ("w", w.w), ("depth", w.depth)):
            a = np.asarray(d["raw"][k], float).copy()
            a[sel] = v
            d["raw"][k] = a
        walk = np.asarray(d["walk"]).copy()
        walk[sel] = w.walk
        d["walk"] = walk
        if w.cat == "median":
            median = np.asarray(d["median"]).copy()
            median[sel] = True
            d["median"] = median
        if d.get("verge") is not None:
            vg = np.asarray(d["verge"], float).copy()
            vg[sel] = w.verge
            dv = 0.5 * np.diff(c.line.s)                # the clamp of assign_sides: <= 1 m of width per 2 m
            for i in range(1, n):
                vg[i] = min(vg[i], vg[i - 1] + dv[i - 1])
            for i in range(n - 2, -1, -1):
                vg[i] = min(vg[i], vg[i + 1] + dv[i])
            d["verge"] = vg
        f.applied_m = float(abs(c.line.s[sel[-1]] - c.line.s[sel[0]]))
    return [f.report() for f in fixes]
