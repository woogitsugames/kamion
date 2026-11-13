"""Routing graph of one region (KRTG v2) for the in-game GPS (ADR 0150).

Inputs (all in git, no network):
  Data/Regions/<id>/roads.graph.json       road graph with provenance (OSM ODbL + BDOT10k), EPSG:2180
  Data/Regions/<id>/region.yaml            origin of the region-local frame (E = x - origin.x, N = y - origin.y)
  Data/Regions/<id>/turn_restrictions.json OSM type=restriction relations touching the region's ways
                                           (refreshed from the cached Geofabrik extract with --refresh-restrictions;
                                           needs pyosmium, run through `uv run --project tools/worldgen`)
  Data/Regions/<id>/overrides.yaml         authored placements (center_offset etc.); together with roads.graph.json
                                           it rebuilds the GENERATED carriageway axes via roads.pipeline.build_network
                                           (the same chain centre lines the world meshes are built from, after
                                           align_forks / abreast_forks shifts - ADR 0144 open item). Edge geometry is
                                           taken from that axis when available (fallback: the raw OSM axis); the
                                           stored length_m (the A* cost) always stays the OSM polyline length.
                                           --no-carriageway-axis disables this.
Output:
  game/Assets/_Project/UI/Resources/CabDisplay/Nav/<id>_route.bytes  (little endian)

  "KRTG" u16 version (2; 1 = no limit fields, no lane section)
  u16 nNames, nNames x (u16 len, utf8)                     street names (index 0 = "")
  u32 nNodes, nNodes x (f32 e, f32 n, u8 flags)            flags bit0 boundary (edge leaves the region data),
                                                          bit1 off-reach (no directed path to it from the main
                                                          strongly connected component - M27, ADR 0150)
  u32 nEdges, nEdges x (u32 from, u32 to, f32 length_m, u8 class, u8 flags, u16 name, u8 maxspeed_kmh,
                        u8 maxspeed_src, u16 nPts, nPts x (f32 e, f32 n))
  v2 only, per edge, before nPts: u16 maxweight (0.01 t), u16 maxaxleload (0.01 t), u16 maxheight (cm),
                        u16 maxlength (cm); 0 = no limit. Normalised from the OSM tags maxweight:hgv (else
                        maxweight), maxaxleload, maxheight, maxlength ("3.5", "3.5 t", "3500 kg", "4 m",
                        "12'6\""; "none" / "default" / unparsable = no limit).
  u16 nRestr, nRestr x (u32 fromEdge, u32 viaNode, u32 toEdge, u8 kind)   kind 0 = no_*, 1 = only_*
  version >= 2, lanes (only edges with a turn:lanes* / lanes* tag):
  u32 nLanes, nLanes x (u32 edge, u8 nFwd, u8 nBwd, nFwd + nBwd x u8 laneMask)   edges in ascending order;
    masks of the stored forward direction (from -> to, after any oneway=-1 reversal) first, then backward.

Edge flags: bit0 oneway (travel only from -> to; oneway=-1 is reversed here), bit1 roundabout, bit2 no trucks
(access=no, hgv=no, service=emergency_access), bit3 restricted access (private / destination / customers / delivery,
service=driveway: allowed only as first / last edge), bit4 *_link, bit5 (v2) hgv=destination (trucks only as the
destination edge), bit6 (M27) off-reach (cannot be entered from the main strongly connected component in any allowed
direction - the region clip can cut the only connection, e.g. Olsztyńska/Buska; destinations there are snapped). Both new
flags are plain bits of the existing flag bytes: no format version change, readers that mask only their own bits
(v1/v2) are unaffected. bit7 (ADR 0164) = hgv:conditional with only simple hour conditions ("no @ (22:00-06:00)"):
informational, the planner has no clock and does not block on it; other conditional values are not encoded, they are
listed in the build report (t["hgv_conditional_unparsed"]). The region data has no hgv:conditional tag (UNVERIFIED for
other regions).
Classes: 0 service / living_street / track, 1 residential / unclassified / tertiary, 2 secondary, 3 trunk / primary.
maxspeed_src: 0 default (pipeline default, UNVERIFIED), 1 OSM.
The readers (parse here and RouteGraph.Parse in C#) accept version 1 (no limit fields, no lane section) and 2.
Lane mask bits (OSM Key:turn:lanes, one u8 per lane, leftmost lane first): bit0 left, bit1 slight_left, bit2 through,
bit3 slight_right, bit4 right, bit5 merge_to_left, bit6 merge_to_right, bit7 reverse; 0 = none / empty / no data.
Only OSM-sourced tags. One-way: turn:lanes (else :forward) masks, lanes count. Two-way: only turn:lanes:forward /
:backward and lanes:forward / :backward (they swap when oneway=-1 reverses the stored geometry); a plain turn:lanes or
lanes on a two-way way is not split (ambiguous / total of both directions). Count-only data = masks 0.
Turn restrictions not tagged in OSM are not known: the game treats every other turn as allowed
except U-turns (a 16.5 m combination) - UNVERIFIED against the street.

Usage:
  python tools/worldgen/navgraph/build_route_graph.py --region bialystok-industrial-c
  uv run --project tools/worldgen python tools/worldgen/navgraph/build_route_graph.py --region <id> --refresh-restrictions
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import struct
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT_DIR = os.path.join(REPO, "game", "Assets", "_Project", "UI", "Resources", "CabDisplay", "Nav")
MAGIC = b"KRTG"
VERSION = 2
VERSION_V1 = 1
SUPPORTED_VERSIONS = (1, 2)

# OSM Key:turn:lanes direction bits (wiki OSM "Key:turn"), one u8 mask per lane, leftmost lane first.
LANE_BITS = {
    "left": 1, "slight_left": 2, "through": 4, "slight_right": 8, "right": 16,
    "merge_to_left": 32, "merge_to_right": 64, "reverse": 128,
}


def parse_turn_lanes(value):
    """OSM turn:lanes value -> list of per-lane direction bitmasks (leftmost lane first), or None when untagged.

    Lanes are '|'-separated, directions within a lane ';'-separated (e.g. "left;through|through|right").
    "none" and empty slots = mask 0 (no direction); unknown tokens are ignored (only the wiki values are defined).
    """
    if value is None:
        return None
    lanes = []
    for lane in str(value).split("|"):
        mask = 0
        for tok in lane.split(";"):
            tok = tok.strip()
            if not tok or tok == "none":
                continue
            bit = LANE_BITS.get(tok)
            if bit is not None:
                mask |= bit
        lanes.append(mask)
    return lanes


def _lane_count(value):
    if value is None or value == "":
        return None
    try:
        return max(0, min(255, int(float(value))))
    except (TypeError, ValueError):
        return None


def osm_attr(e: dict, key: str):
    """Attribute value only when it comes from OSM (pipeline defaults, src=default, are not data - UNVERIFIED)."""
    return attr(e, key) if attr_src(e, key) == "osm" else None


def edge_lanes(e: dict, oneway: bool, reversed_way: bool):
    """(fwdMasks, bwdMasks) for the stored edge direction (fwd = from -> to after any oneway=-1 reversal).

    Only OSM-sourced tags are used (454 region edges carry a pipeline-default `lanes`, src=default - not data).
    One-way way: turn:lanes (else turn:lanes:forward) gives the masks, lanes the count; nothing backward.
    Two-way way: only turn:lanes:forward / :backward and lanes:forward / :backward are directional. A plain
    turn:lanes on a two-way way is ambiguous (wiki OSM Key:turn asks for the :forward / :backward suffixes there)
    and a plain lanes is the TOTAL of both directions (wiki Key:lanes) - neither is split (no guidance rather
    than a guess). The way's forward / backward swap when oneway=-1 reversed the stored geometry.
    Count-only data gives masks 0 (direction unknown).
    """
    if oneway:
        masks = parse_turn_lanes(osm_attr(e, "turn:lanes"))
        if masks is None:
            masks = parse_turn_lanes(osm_attr(e, "turn:lanes:backward" if reversed_way else "turn:lanes:forward"))
        n = _lane_count(osm_attr(e, "lanes"))
        if masks is None and n:
            masks = [0] * n
        return (masks or []), []
    fwd_way = parse_turn_lanes(osm_attr(e, "turn:lanes:forward"))
    bwd_way = parse_turn_lanes(osm_attr(e, "turn:lanes:backward"))
    n_f = _lane_count(osm_attr(e, "lanes:forward"))
    n_b = _lane_count(osm_attr(e, "lanes:backward"))
    if fwd_way is None and n_f:
        fwd_way = [0] * n_f
    if bwd_way is None and n_b:
        bwd_way = [0] * n_b
    fwd, bwd = fwd_way or [], bwd_way or []
    return (bwd, fwd) if reversed_way else (fwd, bwd)


CLASS = {
    "service": 0, "living_street": 0, "track": 0,
    "residential": 1, "unclassified": 1, "tertiary": 1, "tertiary_link": 1,
    "secondary": 2, "secondary_link": 2,
    "primary": 3, "primary_link": 3, "trunk": 3, "trunk_link": 3, "motorway": 3, "motorway_link": 3,
}
F_ONEWAY, F_ROUNDABOUT, F_NO_TRUCK, F_RESTRICTED, F_LINK, F_HGV_DESTINATION = 1, 2, 4, 8, 16, 32
F_HGV_TIMED = 128     # edge flag bit7 (ADR 0164): hgv:conditional with simple hour conditions only (informational)
F_OFF_REACH = 64      # edge flag bit6: cannot be entered from the main SCC in any allowed direction (M27)
NF_OFF_REACH = 2      # node flag bit1 (bit0 = boundary): no directed path from the main SCC - "poza zasięgiem"
NO_TRUCK_ACCESS = {"no"}
RESTRICTED_ACCESS = {"private", "destination", "customers", "delivery", "permissive"}

NO_LIMIT = ("", "none", "default", "national")


def parse_weight_t(v) -> float | None:
    """OSM maxweight / maxaxleload value -> tonnes, or None when there is no usable limit.

    Accepts "3.5", "3,5 t", "3.5t", "3500 kg"; "none" / "default" / unparsable -> None.
    """
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in NO_LIMIT:
        return None
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*(kg|kilograms?|t|tonnes?|tons?)?", s)
    if not m:
        return None
    x = float(m.group(1).replace(",", "."))
    return x / 1000.0 if m.group(2) and m.group(2).startswith("k") else x


_COND_ITEM = re.compile(r"\s*(no|destination)\s*@\s*\(?\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*\)?\s*")


def parse_hgv_conditional(v) -> list | None:
    """OSM hgv:conditional -> [(value, start_min, end_min), ...] when EVERY item is a plain hour window, else None.

    Accepts "no @ (22:00-06:00)" and "no @ 22:00-06:00; destination @ (06:00-08:00)". Days ("Mo-Fr"), dates, weights,
    "yes @ ..." and anything else is not parsed (None) - the caller logs it instead of guessing (ADR 0164).
    """
    if v is None or not str(v).strip():
        return None
    out = []
    for item in str(v).split(";"):
        m = _COND_ITEM.fullmatch(item.lower())
        if not m:
            return None
        h0, m0, h1, m1 = int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        if h0 > 24 or h1 > 24 or m0 > 59 or m1 > 59:
            return None
        out.append((m.group(1), h0 * 60 + m0, h1 * 60 + m1))
    return out


def parse_length_m(v) -> float | None:
    """OSM maxheight / maxlength value -> metres, or None when there is no usable limit.

    Accepts "4", "4.0 m", "12'6\"" (feet'inches); "none" / "default" / unparsable -> None.
    """
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in NO_LIMIT:
        return None
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*(m|metres?|meters?)?", s)
    if m:
        return float(m.group(1).replace(",", "."))
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*'\s*(?:(\d+(?:[.,]\d+)?)\s*\")?", s)
    if m:
        ft = float(m.group(1).replace(",", "."))
        inch = float(m.group(2).replace(",", ".")) if m.group(2) else 0.0
        return ft * 0.3048 + inch * 0.0254
    return None


def to_c(v: float | None, scale: float) -> int:
    """Float in SI units -> stored integer (0 = no limit), clamped to u16."""
    return 0 if v is None else max(0, min(65535, round(v * scale)))


def read_origin(region_dir: str) -> tuple[float, float]:
    ox = oy = None
    in_origin = False
    with open(os.path.join(region_dir, "region.yaml"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("origin:"):
                in_origin = True
                continue
            if in_origin:
                if not line.startswith(" "):
                    break
                k, _, v = line.strip().partition(":")
                if k == "x":
                    ox = float(v)
                elif k == "y":
                    oy = float(v)
    if ox is None or oy is None:
        raise SystemExit("origin not found in region.yaml")
    return ox, oy


def attr(edge: dict, key: str, default=None):
    a = edge.get("attrs", {}).get(key)
    return a.get("v", default) if isinstance(a, dict) else default


def attr_src(edge: dict, key: str) -> str:
    a = edge.get("attrs", {}).get(key)
    return a.get("src", "") if isinstance(a, dict) else ""


def polyline_length(pts) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


AXIS_DP_TOL_M = 0.05   # WORKING_VALUE: Douglas-Peucker tolerance when thinning the dense (0.5 m) carriageway axis


def _dp(points, tol):
    """Douglas-Peucker on a list of (x, y); endpoints always kept."""
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = points[a]
        bx, by = points[b]
        dx, dy = bx - ax, by - ay
        ll = math.hypot(dx, dy)
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            if ll < 1e-12:      # closed loop: first == last point, measure distance to the point itself
                d = math.hypot(points[i][0] - ax, points[i][1] - ay)
            else:
                d = abs(dy * points[i][0] - dx * points[i][1] + bx * ay - by * ax) / ll
            if d > best:
                best, bi = d, i
        if best > tol:
            keep[bi] = True
            stack.append((a, bi))
            stack.append((bi, b))
    return [p for p, k in zip(points, keep) if k]


def load_carriageway_axes(region: str, graph: dict) -> dict:
    """{graph edge id -> [(e, n), ...]} final carriageway centre line per edge, region-local, in the edge's
    stored from -> to orientation.

    The generated world (chunk meshes, roads_qa) is built from roads.pipeline.build_network: each chain's
    `line` after taper_forks / align_forks / abreast_forks (ADR 0074/0076) and the authored center_offset
    overrides IS the carriageway axis the player sees. Chain `raw_spans` map every graph edge id onto its span
    of the chain (edge id w<way>:<a>-<b> = chain c:w<way>:<a>-<b> + osm_way). The axis is not persisted as a
    polyline in generated/*.json (only QA stats and the glb meshes), so it is rebuilt deterministically from
    roads.graph.json + overrides.yaml. Any failure -> {} (the caller falls back to the raw OSM axis).
    """
    try:
        sys.path.insert(0, os.path.join(REPO, "tools", "worldgen"))
        import numpy as np
        from roads import pipeline          # numpy/shapely/yaml come with the tools/worldgen project
        net, _, _, _ = pipeline.build_network(region, graph)
    except Exception as exc:               # ImportError or a pipeline failure: OSM axes for all edges
        print(f"WARNING: carriageway axes unavailable ({exc!r}); all edges fall back to the raw OSM axis")
        return {}
    axes = {}
    for c in net.chains:
        if c.line is None:
            continue
        k = c.length / max(c.raw_spans[-1][1], 1e-9)      # raw span arc length -> dense line arc length
        s, p = c.line.s, c.line.p
        for s0, s1, eid, rev in c.raw_spans:
            i0 = int(np.searchsorted(s, s0 * k))
            i1 = int(np.searchsorted(s, s1 * k, side="right"))
            seg = p[i0:i1]
            if len(seg) < 2:
                continue
            if rev:                                        # edge runs against the chain: keep from -> to
                seg = seg[::-1]
            ax = _dp([(round(float(x), 3), round(float(y), 3)) for x, y in seg], AXIS_DP_TOL_M)
            if polyline_length(ax) < 1e-3:                 # degenerate span: keep the raw OSM axis
                continue
            axes[eid] = ax
    return axes


def build(graph: dict, origin: tuple[float, float], restrictions: list[dict], axes: dict | None = None) -> dict:
    """Pure transform: road graph JSON -> routing graph tables (lists), deterministic order.

    axes (optional): {edge id -> carriageway axis pts, from -> to}, see load_carriageway_axes. When an edge has
    an axis, its stored geometry is the axis (the line the player sees on the minimap / GPS); the stored length
    stays the OSM polyline length, so topology AND the A* cost are unchanged (ADR 0144 open item)."""
    ox, oy = origin
    names = [""]
    name_idx = {"": 0}

    def name_id(n: str) -> int:
        n = n or ""
        if n not in name_idx:
            name_idx[n] = len(names)
            names.append(n)
        return name_idx[n]

    node_ids = sorted(n["id"] for n in graph["nodes"])
    node_index = {nid: i for i, nid in enumerate(node_ids)}
    by_id = {n["id"]: n for n in graph["nodes"]}
    nodes = [(round(by_id[nid]["x"] - ox, 3), round(by_id[nid]["y"] - oy, 3), 1 if by_id[nid].get("boundary") else 0)
             for nid in node_ids]
    osm_node_to_idx = {by_id[nid]["osm_node"]: node_index[nid] for nid in node_ids if "osm_node" in by_id[nid]}

    edges = []
    skipped = 0
    cond_unparsed: list = []
    for e in sorted(graph["edges"], key=lambda e: e["id"]):
        hw = attr(e, "highway", "service")
        cls = CLASS.get(hw)
        if cls is None:
            skipped += 1
            continue
        geom = e["geometry"]
        if isinstance(geom, str):
            geom = json.loads(geom)
        geom_pts = [(round(x - ox, 3), round(y - oy, 3)) for x, y in geom]
        pts = list(geom_pts)
        a, b = node_index[e["from"]], node_index[e["to"]]
        ow = str(attr(e, "oneway", "no"))
        flags = 0
        if ow in ("yes", "true", "1", "-1"):
            flags |= F_ONEWAY
        if ow == "-1":
            pts.reverse()
            a, b = b, a
        ax = axes.get(e["id"]) if axes else None
        if ax is not None:
            pts = list(reversed(ax)) if ow == "-1" else list(ax)   # axis is stored from -> to like the edge
        if attr(e, "junction") in ("roundabout", "circular"):
            flags |= F_ROUNDABOUT | F_ONEWAY   # OSM: roundabouts imply oneway
        # the backward direction of a one-way edge (roundabouts included) is never driven: no backward lanes
        fwd_lanes, bwd_lanes = edge_lanes(e, bool(flags & F_ONEWAY), ow == "-1")
        access = str(attr(e, "access", "") or "")
        hgv = str(attr(e, "hgv", "") or "")
        if access in NO_TRUCK_ACCESS or hgv == "no" or attr(e, "service") == "emergency_access":
            flags |= F_NO_TRUCK
        elif access in RESTRICTED_ACCESS or attr(e, "service") == "driveway":
            flags |= F_RESTRICTED
        if hgv == "destination":
            flags |= F_HGV_DESTINATION   # trucks may enter only to reach a destination on this edge
        if hw.endswith("_link"):
            flags |= F_LINK
        ms = attr(e, "maxspeed", 0) or 0
        try:
            ms = int(float(ms))
        except (TypeError, ValueError):
            ms = 0
        ms_src = 1 if attr_src(e, "maxspeed") == "osm" else 0
        cond = osm_attr(e, "hgv:conditional")
        if cond:
            if parse_hgv_conditional(cond) is not None:
                flags |= F_HGV_TIMED
            else:
                cond_unparsed.append((e["id"], str(cond)))
        mw = parse_weight_t(osm_attr(e, "maxweight:hgv"))
        if mw is None:
            mw = parse_weight_t(osm_attr(e, "maxweight"))
        length = round(polyline_length(geom_pts), 3)   # A* cost: OSM polyline length, not the shifted axis length
        edges.append({
            "id": e["id"], "osm_way": e.get("osm_way"), "from": a, "to": b, "length": length, "class": cls,
            "flags": flags, "name": name_id(attr(e, "name", "") or ""), "maxspeed": max(0, min(255, ms)),
            "maxspeed_src": ms_src, "pts": pts, "lanes": (fwd_lanes, bwd_lanes),
            "maxweight_c": to_c(mw, 100.0), "maxaxleload_c": to_c(parse_weight_t(osm_attr(e, "maxaxleload")), 100.0),
            "maxheight_cm": to_c(parse_length_m(osm_attr(e, "maxheight")), 100.0),
            "maxlength_cm": to_c(parse_length_m(osm_attr(e, "maxlength")), 100.0),
        })

    # Turn restrictions: OSM (from way, via node, to way) -> (from edge, via node, to edge) on the split edges.
    restr = []
    unmapped = []
    for r in restrictions:
        via = osm_node_to_idx.get(r.get("via_node"))
        kind = r.get("restriction", "")
        if via is None or not (kind.startswith("no_") or kind.startswith("only_")):
            unmapped.append(r.get("id"))
            continue
        fe = [i for i, e in enumerate(edges) if e["osm_way"] == r["from_way"] and via in (e["from"], e["to"])]
        te = [i for i, e in enumerate(edges) if e["osm_way"] == r["to_way"] and via in (e["from"], e["to"])]
        if not fe or not te:
            unmapped.append(r.get("id"))
            continue
        for f in fe:
            for t in te:
                if f == t and kind != "no_u_turn":
                    continue
                restr.append((f, via, t, 0 if kind.startswith("no_") else 1))
    restr = sorted(set(restr))
    t = {"names": names, "nodes": nodes, "edges": edges, "restrictions": restr, "unmapped_restrictions": unmapped,
         "skipped_edges": skipped, "hgv_conditional_unparsed": cond_unparsed}
    t["reachability"] = mark_reachability(t)
    return t


def strongly_connected_components(n_nodes: int, edges: list) -> tuple[list, list]:
    """Tarjan SCCs (iterative) of the directed routing graph: from -> to always, to -> from only when not one-way.

    Returns (components, comp) - components sorted by size (desc, ties by smallest node index; deterministic), comp[v]
    = component index of node v (0 = the main / largest one)."""
    adj = [[] for _ in range(n_nodes)]
    for e in edges:
        adj[e["from"]].append(e["to"])
        if not (e["flags"] & F_ONEWAY):
            adj[e["to"]].append(e["from"])
    index = [-1] * n_nodes
    low = [0] * n_nodes
    on_stack = [False] * n_nodes
    stack = []
    comp = [-1] * n_nodes
    comps = []
    counter = 0
    for root in range(n_nodes):
        if index[root] != -1:
            continue
        work = [(root, 0)]
        while work:
            v, pi = work[-1]
            if pi == 0:
                index[v] = low[v] = counter
                counter += 1
                stack.append(v)
                on_stack[v] = True
            descend = False
            for i in range(pi, len(adj[v])):
                w = adj[v][i]
                if index[w] == -1:
                    work[-1] = (v, i + 1)
                    work.append((w, 0))
                    descend = True
                    break
                if on_stack[w] and index[w] < low[v]:
                    low[v] = index[w]
            if descend:
                continue
            if low[v] == index[v]:
                c = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    comp[w] = len(comps)
                    c.append(w)
                    if w == v:
                        break
                comps.append(c)
            work.pop()
            if work:
                u = work[-1][0]
                if low[v] < low[u]:
                    low[u] = low[v]
    order = sorted(range(len(comps)), key=lambda i: (-len(comps[i]), min(comps[i])))
    remap = {old: new for new, old in enumerate(order)}
    comp = [remap[c] for c in comp]
    comps = [comps[i] for i in order]
    return comps, comp


def mark_reachability(t: dict) -> dict:
    """Off-reach marks: nodes / edges the truck cannot DRIVE TO from the main (largest) strongly connected component
    of the directed graph (node flag bit1, edge flag bit6 - plain bits of the existing flag bytes, no format change).

    The 2 km region clip can cut the only connection of a part (ADR 0150: Olsztyńska/Buska) - such parts got
    "Brak dojazdu"; flagged, the game snaps the destination to the reachable part instead.
    Integration r5: "outside the main SCC" alone (PR #29) also flagged every one-way carriageway that leaves the tile
    (reachable, just no way back inside the clip - 144 edges incl. al. Tysiąclecia / Andersa / Maczka) and every
    one-way entry from the tile edge (where the truck may start). Off-reach is therefore the complement of the
    FORWARD closure of the main SCC: a node is off-reach when no directed path leads to it from the main SCC; an
    edge when it cannot be entered in any allowed direction (one-way: from-node unreachable; two-way: both ends).
    Returns the report dict (also stored as t["reachability"])."""
    n = len(t["nodes"])
    comps, comp = strongly_connected_components(n, t["edges"])
    adj = [[] for _ in range(n)]
    for e in t["edges"]:
        adj[e["from"]].append(e["to"])
        if not (e["flags"] & F_ONEWAY):
            adj[e["to"]].append(e["from"])
    reach = [False] * n
    stack = list(comps[0])
    for v in stack:
        reach[v] = True
    while stack:
        v = stack.pop()
        for w in adj[v]:
            if not reach[w]:
                reach[w] = True
                stack.append(w)

    def off(e):
        if e["flags"] & F_ONEWAY:
            return not reach[e["from"]]
        return not reach[e["from"]] and not reach[e["to"]]

    t["nodes"] = [(x, y, f | (NF_OFF_REACH if not reach[i] else 0)) for i, (x, y, f) in enumerate(t["nodes"])]
    for e in t["edges"]:
        if off(e):
            e["flags"] |= F_OFF_REACH
    return {
        "components": len(comps),
        "component_sizes": [len(c) for c in comps],
        "main_nodes": len(comps[0]),
        "main_edges": sum(1 for e in t["edges"] if comp[e["from"]] == 0 and comp[e["to"]] == 0),
        "scc_off_nodes": n - len(comps[0]),
        "off_nodes": sum(1 for r in reach if not r),
        "off_edges": sum(1 for e in t["edges"] if e["flags"] & F_OFF_REACH),
        "off_streets": sorted({t["names"][e["name"]] for e in t["edges"] if (e["flags"] & F_OFF_REACH) and e["name"]}),
    }


def serialize(t: dict, version: int = VERSION) -> bytes:
    """version=2 (default): four truck-limit fields per edge + the lane section; version=1: the old layout (limits and
    lanes dropped; kept to compare against a committed v1 file and to test the readers' backward compatibility)."""
    if version not in SUPPORTED_VERSIONS:
        raise ValueError(f"version {version}")
    out = bytearray()
    out += MAGIC + struct.pack("<H", version)
    if len(t["names"]) > 65535 or len(t["restrictions"]) > 65535:
        raise SystemExit("too many names / restrictions for u16 counts")
    out += struct.pack("<H", len(t["names"]))
    for n in t["names"]:
        b = n.encode("utf-8")
        out += struct.pack("<H", len(b)) + b
    out += struct.pack("<I", len(t["nodes"]))
    for e, n, f in t["nodes"]:
        out += struct.pack("<ffB", e, n, f)
    out += struct.pack("<I", len(t["edges"]))
    for e in t["edges"]:
        out += struct.pack("<IIfBBHBBH", e["from"], e["to"], e["length"], e["class"], e["flags"], e["name"],
                           e["maxspeed"], e["maxspeed_src"], len(e["pts"]))
        if version >= 2:
            out += struct.pack("<HHHH", e["maxweight_c"], e["maxaxleload_c"], e["maxheight_cm"], e["maxlength_cm"])
        for x, y in e["pts"]:
            out += struct.pack("<ff", x, y)
    out += struct.pack("<H", len(t["restrictions"]))
    for f, v, to, k in t["restrictions"]:
        out += struct.pack("<IIIB", f, v, to, k)
    if version >= 2:
        blocks = [(i, e["lanes"]) for i, e in enumerate(t["edges"]) if e["lanes"][0] or e["lanes"][1]]
        out += struct.pack("<I", len(blocks))
        for i, (fwd, bwd) in blocks:
            out += struct.pack("<IBB", i, len(fwd), len(bwd))
            for m in fwd:
                out += struct.pack("<B", m)
            for m in bwd:
                out += struct.pack("<B", m)
    return bytes(out)


def parse(data: bytes) -> dict:
    """Reader (tests and QA): inverse of serialize."""
    o = 0

    def take(fmt):
        nonlocal o
        v = struct.unpack_from(fmt, data, o)
        o += struct.calcsize(fmt)
        return v

    if data[:4] != MAGIC:
        raise ValueError("not KRTG")
    o = 4
    (ver,) = take("<H")
    if ver not in SUPPORTED_VERSIONS:
        raise ValueError(f"version {ver}")
    (nn,) = take("<H")
    names = []
    for _ in range(nn):
        (ln,) = take("<H")
        names.append(data[o:o + ln].decode("utf-8"))
        o += ln
    (nnodes,) = take("<I")
    nodes = [take("<ffB") for _ in range(nnodes)]
    (ne,) = take("<I")
    edges = []
    for _ in range(ne):
        a, b, length, cls, flags, name, ms, mss, npts = take("<IIfBBHBBH")
        mw, mal, mh, ml = (take("<HHHH") if ver >= 2 else (0, 0, 0, 0))
        pts = [take("<ff") for _ in range(npts)]
        edges.append({"from": a, "to": b, "length": length, "class": cls, "flags": flags, "name": name,
                      "maxspeed": ms, "maxspeed_src": mss, "pts": pts, "maxweight_c": mw, "maxaxleload_c": mal,
                      "maxheight_cm": mh, "maxlength_cm": ml})
    (nr,) = take("<H")
    restr = [take("<IIIB") for _ in range(nr)]
    lanes = {}
    if ver >= 2:
        (nl,) = take("<I")
        for _ in range(nl):
            ei, nf, nb = take("<IBB")
            if ei >= len(edges):
                raise ValueError("lane block edge out of range")
            fwd = [take("<B")[0] for _ in range(nf)]
            bwd = [take("<B")[0] for _ in range(nb)]
            lanes[ei] = (fwd, bwd)
    if o != len(data):
        raise ValueError("trailing bytes")
    for i, e in enumerate(edges):
        e["lanes"] = lanes.get(i, ([], []))
    return {"names": names, "nodes": nodes, "edges": edges, "restrictions": restr, "lanes": lanes, "version": ver}


def refresh_restrictions(region_dir: str, graph: dict, pbf: str | None = None) -> list[dict]:
    """Reads type=restriction relations touching the region's ways from the cached Geofabrik extract (pyosmium)."""
    import osmium  # noqa: PLC0415  (only for the refresh)

    pbf_dir = os.path.join(REPO, "Data", "raw", "osm")
    if pbf:
        pbf_dir, pbfs = os.path.dirname(pbf), [os.path.basename(pbf)]
    else:
        pbfs = sorted(p for p in os.listdir(pbf_dir) if p.endswith(".osm.pbf")) if os.path.isdir(pbf_dir) else []
    if not pbfs:
        raise SystemExit(f"no .osm.pbf in {pbf_dir}: run tools/worldgen/fetch_osm.py first")
    pbf = os.path.join(pbf_dir, pbfs[-1])
    ways = {e.get("osm_way") for e in graph["edges"]}
    rows = []
    for rel in osmium.FileProcessor(pbf, osmium.osm.RELATION):
        tags = dict(rel.tags)
        if tags.get("type") != "restriction":
            continue
        kind = tags.get("restriction") or tags.get("restriction:hgv") or ""
        mem = [(m.type, m.ref, m.role) for m in rel.members]
        fw = [r for t, r, role in mem if t == "w" and role == "from"]
        tw = [r for t, r, role in mem if t == "w" and role == "to"]
        vn = [r for t, r, role in mem if t == "n" and role == "via"]
        if not any(w in ways for w in fw + tw):
            continue
        rows.append({"id": rel.id, "restriction": kind, "hgv_only": "restriction:hgv" in tags and "restriction" not in tags,
                     "from_way": fw[0] if fw else None, "to_way": tw[0] if tw else None,
                     "via_node": vn[0] if len(vn) == 1 else None, "via_is_way": any(t == "w" and role == "via" for t, _, role in mem)})
    rows.sort(key=lambda r: r["id"])
    sha = hashlib.sha256(open(pbf, "rb").read()).hexdigest()
    doc = {"schema": "truck-sim-pl/turn-restrictions/1", "source": os.path.basename(pbf), "source_sha256": sha,
           "license": "ODbL 1.0, © OpenStreetMap contributors",
           "note": "OSM type=restriction relations touching the region's ways. Turns without a relation are NOT verified "
                   "(UNVERIFIED): absence in OSM does not mean the turn is legal.",
           "restrictions": rows}
    with open(os.path.join(region_dir, "turn_restrictions.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--refresh-restrictions", action="store_true")
    ap.add_argument("--out-dir", default=OUT_DIR)
    ap.add_argument("--pbf", help="extract to read restrictions from (default: newest Data/raw/osm/*.osm.pbf)")
    ap.add_argument("--no-carriageway-axis", action="store_true",
                    help="keep the raw OSM axes as edge geometry (debug / comparison)")
    args = ap.parse_args(argv)
    rdir = os.path.join(REPO, "Data", "Regions", args.region)
    graph = json.load(open(os.path.join(rdir, "roads.graph.json"), encoding="utf-8"))
    rpath = os.path.join(rdir, "turn_restrictions.json")
    if args.refresh_restrictions:
        rows = refresh_restrictions(rdir, graph, args.pbf)
    elif os.path.exists(rpath):
        rows = json.load(open(rpath, encoding="utf-8"))["restrictions"]
    else:
        rows = []
        print("WARNING: no turn_restrictions.json - all turns treated as allowed (UNVERIFIED)")
    origin = read_origin(rdir)
    axes = {} if args.no_carriageway_axis else load_carriageway_axes(args.region, graph)
    t = build(graph, origin, rows, axes)
    data = serialize(t)
    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, args.region + "_route.bytes")
    with open(path, "wb") as f:
        f.write(data)
    oneway = sum(1 for e in t["edges"] if e["flags"] & F_ONEWAY)
    limited = sum(1 for e in t["edges"] if e["maxweight_c"] or e["maxaxleload_c"] or e["maxheight_cm"] or e["maxlength_cm"])
    hgv_dest = sum(1 for e in t["edges"] if e["flags"] & F_HGV_DESTINATION)
    lane_blocks = sum(1 for e in t["edges"] if e["lanes"][0] or e["lanes"][1])
    lane_dir = sum(1 for e in t["edges"] if any(e["lanes"][0]) or any(e["lanes"][1]))
    print(f"KRTG v{VERSION} {path}: {len(data) / 1024:.1f} KB, nodes {len(t['nodes'])}, edges {len(t['edges'])} "
          f"(oneway {oneway}, skipped {t['skipped_edges']}, carriageway-axis geometry {len(axes)}), "
          f"names {len(t['names'])}, "
          f"restrictions {len(t['restrictions'])} (OSM relations {len(rows)}, unmapped {len(t['unmapped_restrictions'])}), "
          f"limit-tagged edges {limited}, hgv=destination {hgv_dest}, lane blocks {lane_blocks} (with turn directions {lane_dir})")
    timed = sum(1 for e in t["edges"] if e["flags"] & F_HGV_TIMED)
    if timed or t["hgv_conditional_unparsed"]:
        print(f"hgv:conditional: {timed} edges with simple hour windows (flag only), "
              f"{len(t['hgv_conditional_unparsed'])} not parsed (not encoded):")
        for eid, val in t["hgv_conditional_unparsed"]:
            print(f"  UNPARSED hgv:conditional {eid}: {val!r}")
    r = t["reachability"]
    print(f"reachability: {r['components']} strongly connected components (directed, one-way respected); "
          f"main component {r['main_nodes']} nodes / {r['main_edges']} edges; "
          f"off-reach (not drivable to from the main component) {r['off_nodes']} nodes / {r['off_edges']} edges "
          f"(sizes: {', '.join(str(s) for s in r['component_sizes'][:8])}{'...' if len(r['component_sizes']) > 8 else ''})")
    if r["off_streets"]:
        print("off-reach streets: " + ", ".join(r["off_streets"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
